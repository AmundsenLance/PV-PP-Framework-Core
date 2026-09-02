from __future__ import annotations
from copy import deepcopy
from .model import *
from .rng import SemanticRNG
from .ledger import ImmutableLedger
from .grammar import common_action_grammar

class ConformanceError(RuntimeError): pass
class PrimaryExecutionLocked(RuntimeError): pass

class AsterionWorld:
    def __init__(self, master_seed: int=0):
        self.rng=SemanticRNG(master_seed)
        self.ledger=ImmutableLedger()
        self.state=self.initial_state()

    @staticmethod
    def initial_state() -> WorldState:
        a={
            Role.M: AgentState(420, {"assembly":100,"test":100,"engineering":100}, {"s1_boards":160,"kits":150,"finished":20}),
            Role.S1: AgentState(260, {"line":100,"quality":100,"recovery":80}, {"stock":40}),
            Role.S2: AgentState(180, {"line":70,"quality":85,"engineering":75}),
            Role.C: AgentState(0, {"operations":100}),
            Role.L: AgentState(0, {"credit_headroom":100}),
            Role.T: AgentState(0, {"capacity":100}),
            Role.R: AgentState(0, {"regulatory":100}),
        }
        com={
            "COM-CUST": Commitment("COM-CUST", (Role.M,Role.C), "customer_delivery", 80, 0, None),
            "COM-S1": Commitment("COM-S1", (Role.S1,Role.M), "board_supply", 90, 0, None),
        }
        return WorldState(period=0, agents=a, commitments=com)

    def packet(self, role: Role, kind: PacketKind=PacketKind.PRE) -> Packet:
        if kind is PacketKind.ORACLE:
            raise ConformanceError("ORACLE packets may only be constructed by OracleDiagnostic")
        ev=tuple(e for e in self.state.evidence if e.recipient in (role,"ALL") and not (e.claim_family=="accepted_recovery_agreement" and int(e.payload.get("expires_after_period",10**9)) < self.state.period))
        com=tuple(c for c in self.state.commitments.values() if role in c.parties and c.active)
        obs=self._direct_observations(role)
        return Packet(kind, role, self.state.period, ev, com, obs, common_action_grammar(role), {})

    def _direct_observations(self, role: Role):
        s=self.state
        if role is Role.M:
            m=s.agents[Role.M]
            return {"cash_k":m.cash_k,"inventory":dict(m.inventory),"own_pp":dict(m.pp),"customer_reserve":s.customer_reserve,"s2_qualified":s.s2_qualified,"s2_conditional":s.s2_emergency_conditional,"s2_external_encumbrance":s.s2_external_encumbrance,"m_covenant_headroom":getattr(s,"m_covenant_headroom",1.0),"transport_state":s.transport_state,"benchmark_end_period":16,"m_line_shutdown":bool(getattr(s,"m_line_shutdown",False)),"termination_eligible":bool(getattr(s,"customer_termination_eligible",False)),"breach_strikes":len(getattr(s,"breach_strikes",[])),"s1_suspect_boards":float(getattr(s,"s1_suspect_boards",0.0))}
        a=s.agents[role]
        obs={"cash_k":a.cash_k,"own_pp":dict(a.pp),"inventory":dict(a.inventory)}
        if role is Role.C:
            obs.update(customer_reserve=s.customer_reserve, customer_demand=s.customer_demand,
                       customer_terminated=s.customer_terminated, current_customer_commitment=getattr(s,"current_customer_commitment",80),
                       termination_eligible=bool(getattr(s,"customer_termination_eligible",False)),
                       breach_strikes=len(getattr(s,"breach_strikes",[])))
        elif role is Role.L:
            obs.update(m_credit_available_k=getattr(s,"m_credit_available_k",500.0),
                       m_covenant_headroom=getattr(s,"m_covenant_headroom",1.0),
                       m_cash_k=s.agents[Role.M].cash_k)
        elif role is Role.T:
            obs.update(transport_state=s.transport_state, pending_transport=len(getattr(s,"pending_transport",[])),
                       transport_reservations=tuple(dict(x) for x in getattr(s,"transport_reservations",[])))
        elif role is Role.S1:
            obs.update(s1_containment_active=bool(getattr(s,"s1_containment_active",False)))
        elif role is Role.S2:
            obs.update(s2_qualified=s.s2_qualified, s2_conditional=s.s2_emergency_conditional,
                       s2_external_encumbrance=s.s2_external_encumbrance, r_emergency_active=s.r_emergency_active)
        return obs

    def deteriorate_s1(self, period: int, line_dec=15, quality_dec=20):
        s1=self.state.agents[Role.S1]
        s1.pp["line"]=max(0,s1.pp["line"]-line_dec)
        s1.pp["quality"]=max(0,s1.pp["quality"]-quality_dec)
        self.ledger.append(period,"exogenous_s1_deterioration",line_dec=line_dec,quality_dec=quality_dec)

    def s1_message(self, period: int) -> Evidence:
        s1=self.state.agents[Role.S1]
        if s1.pp["line"]>=70 and s1.pp["quality"]>=70:
            mode="exact"
        else:
            mode=self.rng.choice(["exact","temporary","optimistic"],[.40,.35,.25],"s1_message",period,"S1","M")
        payload={"mode":mode}
        if mode=="exact": payload.update(line=s1.pp["line"],quality=s1.pp["quality"])
        elif mode=="temporary": payload.update(text="temporary issue")
        else: payload.update(text="optimistic ETA",eta_bias_weeks=-1)
        e=Evidence(f"E-S1-{period}-{mode}",period,Role.S1,Role.M,"supplier_status",payload,EvidenceStatus.REPORTED)
        self.state.evidence.append(e); self.ledger.append(period,"message",evidence_id=e.evidence_id,mode=mode)
        return e

    def start_s2_qualification(self, emergency=False):
        m=self.state.agents[Role.M]
        if m.cash_k < 35: raise ConformanceError("insufficient cash")
        # v0.4 separates the $35k launch transformation from weekly qualification stages.
        # Engineering/test encumbrance and the $20k stage cost occur only when a stage executes.
        m.cash_k -= 35
        self.ledger.append(self.state.period,"s2_qualification_started",emergency=emergency,cash_cost_k=35)

    @staticmethod
    def s2_defect_probability(quality_pp: float) -> float:
        """V2 prospective calibration: Q=70 -> 2%, Q=85 -> 1%, Q=100 -> 0%.

        The same linear relation continues below 70 and is clamped to [0,1]. This is a
        benchmark calibration, not an empirical electronics-manufacturing estimate.
        """
        return min(1.0, max(0.0, (100.0-float(quality_pp))/1500.0))

    def sample_s2_qualification_stage(self, emergency=False):
        """Realize one frozen 20-board S2 qualification stage under V2 calibration.

        True defects follow the PP-linked defect rate. Among true defects, 80% are
        critical and 20% noncritical. The frozen test has 90% sensitivity and 99%
        specificity. A false positive on an actually good board is counted as a
        noncritical detected defect because no true functional/critical failure exists.
        """
        s=self.state; quality=float(s.agents[Role.S2].pp.get("quality",0.0))
        p_defect=self.s2_defect_probability(quality)
        critical_detected=0; noncritical_detected=0
        true_critical=0; true_noncritical=0; false_positives=0
        stage_no=int(s.s2_qualification_stages)+1
        for i in range(20):
            defective=self.rng.uniform01("s2_true_defect",s.period,stage_no,i) < p_defect
            if defective:
                critical=self.rng.uniform01("s2_defect_criticality",s.period,stage_no,i) < .80
                if critical: true_critical += 1
                else: true_noncritical += 1
                detected=self.rng.uniform01("s2_test_detection",s.period,stage_no,i) < .90
                if detected:
                    if critical: critical_detected += 1
                    else: noncritical_detected += 1
            else:
                false_positive=self.rng.uniform01("s2_test_false_positive",s.period,stage_no,i) < .01
                if false_positive:
                    false_positives += 1; noncritical_detected += 1
        passed=self.complete_s2_stage(critical_detected,noncritical_detected,emergency)
        self.ledger.append(s.period,"s2_qualification_sample",stage=stage_no,sample_size=20,quality_pp=quality,defect_probability=p_defect,true_critical=true_critical,true_noncritical=true_noncritical,false_positives=false_positives,critical_detected=critical_detected,noncritical_detected=noncritical_detected,passed=passed)
        return passed

    def complete_s2_stage(self, critical_detected=0, noncritical_detected=0, emergency=False):
        quality=float(self.state.agents[Role.S2].pp.get("quality",0.0))
        # v0.4: quality below 70 is itself a failed stage/corrective-stage condition.
        fail = quality<70 or critical_detected>0 or noncritical_detected>=2
        self.ledger.append(self.state.period,"s2_qualification_stage",critical=critical_detected,noncritical=noncritical_detected,quality_pp=quality,passed=not fail)
        if not fail:
            self.state.s2_qualification_stages += 1
        required=2 if emergency else 4
        if self.state.s2_qualification_stages>=required and quality>=70:
            self.state.s2_qualified=True
            self.state.s2_emergency_conditional=emergency
        return not fail

    @staticmethod
    def transport_reliability(state: str) -> float:
        try:
            return {"LOW":.96,"MEDIUM":.90,"HIGH":.82}[str(state).upper()]
        except KeyError as exc:
            raise ConformanceError(f"unknown transport state {state}") from exc

    def supplier_transport_on_time(self, supplier: Role) -> bool:
        """One draw determines on-time versus exactly one-period-late delivery.

        A late shipment remains in transit and is not rerolled. The semantic key excludes
        controller/regime identifiers so paired regimes share the same event-keyed draw.
        """
        p=self.transport_reliability(self.state.transport_state)
        return self.rng.uniform01("supplier_transport",self.state.period,supplier.value,Role.M.value) < p

    def activate_s2_external_opportunity(self):
        if self.state.period != 6: raise ConformanceError("deterministic opportunity is period 6")
        e=Evidence("E-S2-OPP-P6",6,"EXTERNAL",Role.S2,"external_market_opportunity",{"capacity_risk":30},EvidenceStatus.VERIFIED,True)
        self.state.evidence.append(e); self.ledger.append(6,"s2_external_opportunity")
        return e

    def close_s2_opportunity_if_unreserved(self, reservation_exists: bool):
        if self.state.period != 7: raise ConformanceError("closure decision is end period 7")
        if not reservation_exists:
            self.state.s2_external_encumbrance=30
            self.state.s2_external_encumbrance_until=12
            self.ledger.append(7,"s2_external_encumbrance_scheduled",start_period=8,capacity=30,end_period=12)

    def schedule_delivered_board_failures(self, shipment_id: str, risk_board_ids: dict[str, object]):
        """D8/D10-D12: realize field risk at delivery using stable physical board identities."""
        probs={"ordinary":.20,"shortcut":.08,"full":.015}
        scheduled=0; risk_counts={}
        for provenance in ("ordinary","shortcut","full"):
            raw=risk_board_ids.get(provenance,[])
            if isinstance(raw,int):
                # Backward-compatible test fixture input; production passes stable board IDs.
                board_ids=[f"{shipment_id}:{provenance}:legacy:{i}" for i in range(raw)]
            else:
                board_ids=list(raw)
            risk_counts[provenance]=len(board_ids)
            p=probs[provenance]
            for board_id in board_ids:
                # Key excludes controller/regime and final shipment ordinal. Physical board identity is stable.
                if self.rng.uniform01("delivered_board_field_failure",board_id,provenance) < p:
                    delay=self.rng.choice([2,3,4],[1/3,1/3,1/3],"delivered_board_field_delay",board_id,provenance)
                    self.state.field_failure_queue.append({"batch":shipment_id,"board_id":board_id,"delivery_period":self.state.period,"due":self.state.period+delay,"provenance":provenance,"conditional_p":p})
                    scheduled+=1
        self.ledger.append(self.state.period,"delivered_board_field_risk",shipment_id=shipment_id,risk_counts=risk_counts,risk_board_ids={k:tuple(v) if not isinstance(v,int) else tuple(f"{shipment_id}:{k}:legacy:{i}" for i in range(v)) for k,v in risk_board_ids.items()},scheduled=scheduled,ordinary_p=.20,shortcut_p=.08,full_p=.015)

    def r_emergency_check(self, certified_available_next_two: tuple[float,float], aggregate_commitment: float, safety_containment=False):
        trigger=safety_containment or all(x < .60*aggregate_commitment for x in certified_available_next_two)
        if trigger:
            self.state.r_emergency_active=True
            e=Evidence(f"E-R-EM-{self.state.period}",self.state.period,Role.R,"ALL","emergency_qualification_notice",{"active":True},EvidenceStatus.VERIFIED,True)
            self.state.evidence.append(e); self.ledger.append(self.state.period,"r_emergency_activated")
        return trigger

    def advance_period(self):
        s=self.state
        # v0.14 recovery-agreement evidence protects the acceptance period and the next period only.
        s.evidence=[e for e in s.evidence if not (e.claim_family=="accepted_recovery_agreement" and int(e.payload.get("expires_after_period",10**9)) < self.state.period)]
        # v0.13 objective supplier terminal transitions are world-side, not controller choices.
        s1=s.agents[Role.S1]
        low=bool(s1.cash_k<=0 and float(s1.pp.get("line",0))<25)
        s.__dict__["s1_low_cash_line_weeks"]=(int(getattr(s,"s1_low_cash_line_weeks",0))+1) if low else 0
        forced=bool(getattr(s,"s1_containment_active",False))
        s.__dict__["s1_forced_closure_weeks"]=(int(getattr(s,"s1_forced_closure_weeks",0))+1) if forced else 0
        if not s1.exited and (s.s1_low_cash_line_weeks>=2 or s.s1_forced_closure_weeks>=3):
            s1.exited=True
            self.ledger.append(s.period,"s1_exit",reason="cash_line" if s.s1_low_cash_line_weeks>=2 else "forced_closure",irreversible=True)
        s2=s.agents[Role.S2]
        active_s2_contract=any(c.active and Role.S2 in c.parties and c.family in ("s2_qualification","s2_capacity","s2_order") for c in s.commitments.values())
        if not s2.exited and s2.cash_k<30 and not active_s2_contract:
            s2.exited=True
            self.ledger.append(s.period,"s2_exit",reason="cash_below_30_no_active_contract",irreversible=True)
        s.period += 1
        if s.s2_external_encumbrance_until is not None and s.period>s.s2_external_encumbrance_until:
            s.s2_external_encumbrance=0; s.s2_external_encumbrance_until=None
