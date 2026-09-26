from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from math import ceil
from typing import Iterable

from .model import Action, ActionKind, Commitment, Evidence, EvidenceStatus, Role, TransitionResult, WorldState
from .world import AsterionWorld, ConformanceError

@dataclass(frozen=True)
class JointResolution:
    accepted: tuple[Action, ...]
    rejected: tuple[tuple[Action, str], ...]

class AsterionTransitionEngine:
    """Frozen calibration/conformance transition engine.

    This engine implements the named action families and period-order invariants needed
    by the pre-freeze conformance package. It is intentionally unavailable to the
    primary comparative runner until the Calibration Lock Record changes the lock.
    """
    def __init__(self, world: AsterionWorld):
        self.world = world
        s = self.world.state
        # Runtime fields are attached explicitly so earlier serialized fixture objects remain readable.
        s.__dict__.setdefault("m_credit_available_k", 500.0)
        s.__dict__.setdefault("m_covenant_headroom", 1.0)
        s.__dict__.setdefault("m_weekly_debt_burden_k", 0.0)
        s.__dict__.setdefault("breach_strikes", [])
        s.__dict__.setdefault("consecutive_good_delivery_weeks", 0)
        s.__dict__.setdefault("m_overload_weeks", 0)
        s.__dict__.setdefault("pending_receipts", [])
        s.__dict__.setdefault("pending_full_rework", [])
        # M11 D7/D8 conserved S1 quality/provenance state.
        m=s.agents[Role.M]
        initial_s1=float(m.inventory.get("s1_boards",0))
        s.__dict__.setdefault("s1_clean_boards", initial_s1)
        s.__dict__.setdefault("s1_latent_defect_boards", 0.0)
        s.__dict__.setdefault("s1_shortcut_reworked_boards", 0.0)
        s.__dict__.setdefault("s1_full_reworked_boards", 0.0)
        s.__dict__.setdefault("s1_suspect_boards", 0.0)
        s.__dict__.setdefault("s1_suspect_board_ids", [])
        s.__dict__.setdefault("current_s1_inspection_rate", .20)
        s.__dict__.setdefault("finished_s1_clean", 0.0)
        s.__dict__.setdefault("finished_s1_latent", 0.0)
        s.__dict__.setdefault("finished_s1_shortcut", 0.0)
        s.__dict__.setdefault("finished_s1_full", 0.0)
        # M12 D9 physical FIFO cohort queues. Hidden provenance is carried inside cohorts
        # but never used to choose which usable board is consumed next.
        s.__dict__.setdefault("s1_usable_cohorts", [{"source":"initial","period":s.period,"provenance":"clean","units":initial_s1}] if initial_s1 else [])
        s.__dict__.setdefault("finished_s1_cohorts", [])
        s.__dict__.setdefault("pending_transport", [])
        s.__dict__.setdefault("major_field_events", 0)
        s.__dict__.setdefault("observed_field_failures", [])
        s.__dict__.setdefault("major_field_windows_triggered", [])
        s.__dict__.setdefault("customer_quality_pressure", 0)
        s.__dict__.setdefault("s2_reserved_capacity", 0.0)
        s.__dict__.setdefault("s2_reservation_until", None)
        s.__dict__.setdefault("accepted_proposals", {})
        s.__dict__.setdefault("s1_recovery_active", False)
        s.__dict__.setdefault("s1_assisted_recovery", False)
        s.__dict__.setdefault("current_customer_commitment", 80)
        s.__dict__.setdefault("customer_termination_eligible", False)
        s.__dict__.setdefault("m_line_shutdown", False)
        s.__dict__.setdefault("pending_m_pp_recovery", [])
        s.__dict__.setdefault("transport_reservations", [])

    @property
    def state(self): return self.world.state

    def available_pp(self, role: Role, domain: str) -> float:
        a=self.state.agents[role]
        return max(0.0, float(a.pp.get(domain,0.0))-float(a.encumbered.get(domain,0.0)))

    def validate(self, action: Action) -> str | None:
        s=self.state; a=s.agents[action.actor]
        if a.exited: return "ACTOR_EXITED"
        if action.kind is ActionKind.ROUTINE_PRODUCE:
            n=float(action.params.get("units",0)); m=s.agents[Role.M]
            if action.actor is not Role.M: return "ROLE_INVALID"
            if getattr(s,"m_line_shutdown",False): return "LINE_SHUTDOWN"
            if "s1_units" in action.params or "s2_units" in action.params:
                q1=float(action.params.get("s1_units",0)); q2=float(action.params.get("s2_units",0))
                if q1+q2!=n or q1<0 or q2<0: return "SOURCE_ALLOCATION_INVALID"
                if q1>m.inventory.get("s1_boards",0) or q2>m.inventory.get("s2_boards",0): return "BOARD_SHORTAGE"
                if q2>0 and not s.s2_qualified: return "S2_NOT_QUALIFIED"
            if n<0 or m.inventory.get("s1_boards",0)+m.inventory.get("s2_boards",0)<n: return "BOARD_SHORTAGE"
            if m.inventory.get("kits",0)<n: return "KIT_SHORTAGE"
            if min(self.available_pp(Role.M,"assembly"),self.available_pp(Role.M,"test"))<n: return "CAPACITY_SHORTAGE"
            if m.cash_k < 3*n: return "CASH_SHORTAGE"
        elif action.kind is ActionKind.SHIP:
            n=float(action.params.get("units",0));
            if n<0: return "SHIP_QUANTITY_INVALID"
            if action.actor is Role.M:
                if self.state.agents[Role.M].inventory.get("finished",0)<n: return "FINISHED_SHORTAGE"
                # v0.4 M-SHIP requires accepted T capacity. One outbound pallet-equivalent
                # slot carries up to 20 finished units; a booking is a reservation, not a guarantee.
                need_slots=ceil(n/20) if n>0 else 0
                available=sum(int(x.get("slots",0)) for x in getattr(s,"transport_reservations",[])
                              if int(x.get("period",-1))==s.period and x.get("route","M-C")=="M-C")
                if need_slots>available: return "TRANSPORT_CAPACITY_SHORTAGE"
            if action.actor is Role.S1:
                if bool(getattr(s,"s1_containment_active",False)) or float(s.agents[Role.S1].pp.get("quality",0))<35:
                    return "S1_CONTAINED"
                cap=self.available_pp(Role.S1,"line")+float(s.agents[Role.S1].inventory.get("stock",0))
                if n>min(90.0,cap): return "SUPPLIER_CAPACITY_SHORTAGE"
                if self.state.agents[Role.M].cash_k < 2.0*n: return "BUYER_CASH_SHORTAGE"
            if action.actor is Role.S2:
                if not s.s2_qualified: return "S2_NOT_QUALIFIED"
                cap=max(0.0,self.available_pp(Role.S2,"line")-float(s.s2_external_encumbrance))
                if s.s2_emergency_conditional: cap=min(40.0,cap)
                if n>cap: return "SUPPLIER_CAPACITY_SHORTAGE"
                if self.state.agents[Role.M].cash_k < 2.6*n: return "BUYER_CASH_SHORTAGE"
        elif action.kind is ActionKind.M_CONSERVE:
            if action.actor is not Role.M: return "ROLE_INVALID"
            cap=action.params.get("production_cap")
            if not isinstance(cap,(int,float)) or int(cap)!=cap or cap<0: return "CONSERVE_CAP_INVALID"
            maxn=min(a.inventory.get("s1_boards",0)+a.inventory.get("s2_boards",0),a.inventory.get("kits",0),self.available_pp(Role.M,"assembly"),self.available_pp(Role.M,"test"),max(0,a.cash_k)//3)
            if cap>maxn: return "CONSERVE_CAP_INFEASIBLE"
        elif action.kind is ActionKind.M_RATION:
            if action.actor is not Role.M: return "ROLE_INVALID"
            q=action.params.get("customer_allocation")
            if not isinstance(q,(int,float)) or int(q)!=q or q<0 or q>80: return "RATION_INVALID"
        elif action.kind is ActionKind.M_SPLIT_SOURCE:
            if action.actor is not Role.M: return "ROLE_INVALID"
            q1=action.params.get("s1_units",0); q2=action.params.get("s2_units",0)
            if any(not isinstance(q,(int,float)) or int(q)!=q or q<0 for q in (q1,q2)): return "SPLIT_INVALID"
            if q1>a.inventory.get("s1_boards",0): return "S1_BOARD_SHORTAGE"
            if q2>0 and not s.s2_qualified: return "S2_NOT_QUALIFIED"
            if q2>a.inventory.get("s2_boards",0): return "S2_BOARD_SHORTAGE"
            n=q1+q2
            if n>min(a.inventory.get("kits",0),self.available_pp(Role.M,"assembly"),self.available_pp(Role.M,"test"),max(0,a.cash_k)//3): return "SPLIT_CAPACITY_SHORTAGE"
        elif action.kind is ActionKind.M_BOOK_T:
            if action.actor is not Role.M: return "ROLE_INVALID"
            mode=str(action.params.get("mode","")); slots=action.params.get("slots",0); period=action.params.get("period",s.period)
            if mode not in ("normal","expedite"): return "TRANSPORT_MODE_INVALID"
            if not isinstance(slots,(int,float)) or int(slots)!=slots or slots<1: return "TRANSPORT_SLOTS_INVALID"
            if not isinstance(period,(int,float)) or int(period)!=period or period<s.period or period>16: return "TRANSPORT_PERIOD_INVALID"
            future_state="LOW" if int(period)<5 else ("MEDIUM" if int(period)<9 else ("HIGH" if int(period)<12 else "MEDIUM"))
            caps={"LOW":(6,2),"MEDIUM":(4,2),"HIGH":(3,1)}[future_state]
            cap=caps[0 if mode=="normal" else 1]
            used=sum(int(x.get("slots",0)) for x in getattr(s,"transport_reservations",[]) if x.get("period")==int(period) and x.get("mode")==mode)
            if slots>max(0,cap-used): return "TRANSPORT_CAPACITY_SHORTAGE"
            fee=(4 if mode=="normal" else 12)*int(slots)
            if a.cash_k<fee: return "CASH_SHORTAGE"
        elif action.kind is ActionKind.M_AMEND_L:
            if action.actor is not Role.M: return "ROLE_INVALID"
            if s.m_covenant_headroom>=.25: return "AMENDMENT_NOT_REQUIRED"
            if a.cash_k<30: return "CASH_SHORTAGE"
        elif action.kind is ActionKind.M_RECOVER_PP:
            if action.actor is not Role.M: return "ROLE_INVALID"
            domain=str(action.params.get("domain",""))
            if domain not in ("assembly","test"): return "RECOVERY_DOMAIN_INVALID"
            if a.cash_k<25 or self.available_pp(Role.M,"engineering")<20: return "RECOVERY_RESOURCE_SHORTAGE"
        elif action.kind is ActionKind.M_PAUSE:
            if action.actor is not Role.M: return "ROLE_INVALID"
            if getattr(s,"m_line_shutdown",False): return "LINE_SHUTDOWN"
        elif action.kind is ActionKind.M_BREACH_CONTROLLED:
            if action.actor is not Role.M: return "ROLE_INVALID"
            q=action.params.get("quantity_not_delivered",0)
            if not isinstance(q,(int,float)) or int(q)!=q or q<1 or q>80: return "BREACH_QUANTITY_INVALID"
        elif action.kind is ActionKind.M_SHUT_LINE:
            if action.actor is not Role.M: return "ROLE_INVALID"
            if getattr(s,"m_line_shutdown",False): return "LINE_ALREADY_SHUT"
        elif action.kind is ActionKind.S1_ASSIST:
            if action.actor is not Role.M: return "ROLE_INVALID"
            if a.cash_k<20 or self.available_pp(Role.M,"engineering")<20: return "ASSIST_RESOURCE_SHORTAGE"
        elif action.kind is ActionKind.START_S2_QUAL:
            if action.actor is not Role.M: return "ROLE_INVALID"
            emergency=bool(action.params.get("emergency",False))
            if emergency and not s.r_emergency_active: return "R_EMERGENCY_INACTIVE"
            if a.cash_k<35: return "CASH_SHORTAGE"
        elif action.kind is ActionKind.S2_QUAL_STAGE:
            if action.actor is not Role.S2: return "ROLE_INVALID"
            active=[c for c in s.commitments.values() if c.active and c.family=="s2_qualification" and Role.S2 in c.parties]
            if not active: return "S2_QUALIFICATION_INACTIVE"
            emergency=bool(active[-1].metadata.get("emergency",False))
            m=s.agents[Role.M]; s2=s.agents[Role.S2]
            if m.cash_k<20: return "QUALIFICATION_STAGE_CASH_SHORTAGE"
            if self.available_pp(Role.M,"engineering")<20: return "M_ENGINEERING_SHORTAGE"
            if self.available_pp(Role.S2,"engineering")<20: return "S2_ENGINEERING_SHORTAGE"
            if emergency and self.available_pp(Role.M,"test")<10: return "M_TEST_SHORTAGE"
            if self.available_pp(Role.S2,"line")<20: return "S2_SAMPLE_CAPACITY_SHORTAGE"
        elif action.kind is ActionKind.RESERVE_S2:
            if action.actor is not Role.M: return "ROLE_INVALID"
            cap=float(action.params.get("capacity",60)); duration=int(action.params.get("duration",5))
            if a.cash_k<20: return "CASH_SHORTAGE"
            if cap!=60 or duration!=5: return "RESERVATION_TERMS_INVALID"
            if s.agents[Role.S2].exited: return "S2_EXITED"
            if max(0.0,70.0-float(s.s2_external_encumbrance))<60: return "S2_CAPACITY_UNAVAILABLE"
        elif action.kind is ActionKind.REQUEST_RENEGOTIATION:
            if action.actor is not Role.M: return "ROLE_INVALID"
            q=action.params.get("delivery",action.params.get("quantity"))
            if not isinstance(q,(int,float)) or int(q)!=q or q<60 or q>80: return "RENEGOTIATION_TERMS_INVALID"
            if s.customer_terminated: return "CUSTOMER_TERMINATED"
            if max(0.0,float(s.customer_reserve)+float(q)-80.0)<40.0: return "COUNTERPART_REJECT"
        elif action.kind is ActionKind.ORDER_S1:
            if action.actor is not Role.M: return "ROLE_INVALID"
            q=action.params.get("quantity",0)
            if not isinstance(q,(int,float)) or int(q)!=q or q<0 or q>90: return "ORDER_TERMS_INVALID"
            s1=s.agents[Role.S1]
            available=max(0.0,float(s1.pp.get("line",0))+float(s1.inventory.get("stock",0)))
            if s1.exited or q>min(90.0,available): return "COUNTERPART_REJECT"
        elif action.kind is ActionKind.ORDER_S2:
            if action.actor is not Role.M: return "ROLE_INVALID"
            q=action.params.get("quantity",0)
            if not isinstance(q,(int,float)) or int(q)!=q or q<0: return "ORDER_TERMS_INVALID"
            if not s.s2_qualified: return "S2_NOT_QUALIFIED"
            cap=max(0.0,float(s.agents[Role.S2].pp.get("line",0))-float(s.s2_external_encumbrance))
            if s.s2_emergency_conditional: cap=min(40.0,cap)
            if q>cap: return "COUNTERPART_REJECT"
        elif action.kind is ActionKind.CANCEL:
            if action.actor is not Role.M: return "ROLE_INVALID"
            cid=str(action.params.get("commitment_id",""))
            c=s.commitments.get(cid)
            if c is None or not c.active: return "CANCEL_OBJECT_INVALID"
            if c.start_period<=s.period: return "CANCEL_TOO_LATE"
            if c.family not in ("s2_capacity","s1_order","s2_order","s2_qualification"): return "CANCEL_OBJECT_INVALID"
        elif action.kind in (ActionKind.SHORTCUT_REWORK,ActionKind.FULL_REWORK):
            n=float(action.params.get("units",20)); batches=ceil(n/20)
            cash=(25 if action.kind is ActionKind.SHORTCUT_REWORK else 35)*batches
            test=(10 if action.kind is ActionKind.SHORTCUT_REWORK else 15)*batches
            if a.cash_k<cash or self.available_pp(Role.M,"test")<test: return "REWORK_RESOURCE_SHORTAGE"
            if n>float(getattr(s,"s1_suspect_boards",0.0)): return "REWORK_SUBSTRATE_SHORTAGE"
        elif action.kind is ActionKind.REQUEST_FINANCE:
            amount=float(action.params.get("amount_k",0))
            if amount<=0 or amount%50!=0: return "DRAW_INCREMENT_INVALID"
            if amount>s.m_credit_available_k: return "FACILITY_LIMIT"
        elif action.kind is ActionKind.S1_RECOVER:
            if action.actor is not Role.S1: return "ROLE_INVALID"
            if a.cash_k < 40 or self.available_pp(Role.S1,"recovery") < 25: return "RECOVERY_RESOURCE_SHORTAGE"
        elif action.kind is ActionKind.S1_CONTAIN:
            if action.actor is not Role.S1: return "ROLE_INVALID"
            if float(s.agents[Role.S1].pp.get("quality",0))>=35: return "CONTAINMENT_NOT_TRIGGERED"
        elif action.kind is ActionKind.S1_ACCEPT_ASSIST:
            if action.actor is not Role.S1: return "ROLE_INVALID"
        elif action.kind in (ActionKind.S2_ACCEPT_QUAL,ActionKind.S2_ACCEPT_RES):
            if action.actor is not Role.S2: return "ROLE_INVALID"
        elif action.kind in (ActionKind.C_ACCEPT_RENEG,ActionKind.C_REJECT_RENEG):
            if action.actor is not Role.C: return "ROLE_INVALID"
        elif action.kind in (ActionKind.C_CONTINUE,ActionKind.C_THREATEN,ActionKind.C_TERMINATE):
            if action.actor is not Role.C: return "ROLE_INVALID"
            if action.kind is ActionKind.C_TERMINATE:
                if s.customer_terminated: return "CUSTOMER_TERMINATED"
                # M13: with no alternate supplier, exit means C's own operations have failed.
                # Strike eligibility remains a distress signal but cannot by itself authorize exit.
                if float(s.agents[Role.C].pp.get("operations",100.0))>0.0: return "CUSTOMER_BUSINESS_STILL_VIABLE"
        elif action.kind in (ActionKind.L_APPROVE_DRAW,ActionKind.L_REJECT_DRAW,ActionKind.L_OFFER_AMEND,ActionKind.L_REJECT_AMEND,ActionKind.L_RESTRICT):
            if action.actor is not Role.L: return "ROLE_INVALID"
        elif action.kind in (ActionKind.T_ACCEPT_BOOK,ActionKind.T_REJECT_BOOK,ActionKind.T_EXECUTE):
            if action.actor is not Role.T: return "ROLE_INVALID"
        return None

    def resolve_joint(self, actions: Iterable[Action]) -> JointResolution:
        actions=list(actions); accepted=[]; rejected=[]
        planned_production=sum(float(a.params.get("units",0)) for a in actions if a.actor is Role.M and a.kind is ActionKind.ROUTINE_PRODUCE)
        # Validate against the common within-period action set. Shipment may use finished goods
        # created by a simultaneously accepted production action because production realizes
        # before outbound transfer in the frozen transformation order.
        for action in sorted(actions,key=lambda x:x.action_id):
            reason=self.validate(action)
            if reason=="FINISHED_SHORTAGE" and action.actor is Role.M and action.kind is ActionKind.SHIP:
                need=float(action.params.get("units",0))
                have=float(self.state.agents[Role.M].inventory.get("finished",0))+planned_production
                if have>=need: reason=None
            if reason: rejected.append((action,reason)); continue
            accepted.append(action)
        return JointResolution(tuple(accepted),tuple(rejected))

    def _execute(self, action: Action):
        s=self.state; m=s.agents[Role.M]
        if action.kind is ActionKind.ROUTINE_PRODUCE:
            n=int(action.params.get("units",0))
            if "s1_units" in action.params or "s2_units" in action.params:
                use_s1=int(action.params.get("s1_units",0)); use_s2=int(action.params.get("s2_units",0))
            else:
                use_s2=min(n,m.inventory.get("s2_boards",0) if s.s2_qualified else 0); use_s1=n-use_s2
            m.inventory["s2_boards"]=m.inventory.get("s2_boards",0)-use_s2
            # M12 D9: reconcile any directly seeded aggregate delta as the newest clean cohort,
            # then consume S1 boards strictly by physical FIFO cohort order.
            queued=sum(float(c.get("units",0)) for c in s.s1_usable_cohorts)
            aggregate=float(m.inventory.get("s1_boards",0))
            if aggregate>queued+1e-9:
                s.s1_usable_cohorts.append({"source":"legacy_reconcile","period":s.period,"provenance":"clean","units":aggregate-queued})
                s.s1_clean_boards+=aggregate-queued
            remain=float(use_s1); consumed={"clean":0.0,"latent":0.0,"shortcut":0.0,"full":0.0}
            consumed_cohorts=[]
            while remain>1e-9 and s.s1_usable_cohorts:
                c=s.s1_usable_cohorts[0]; take=min(remain,float(c["units"])); take_i=int(take)
                prov=c["provenance"]; consumed[prov]+=take
                ids=list(c.get("board_ids",[]))
                taken_ids=ids[:take_i] if ids else [f"{c.get('source','legacy')}:board:{i}" for i in range(take_i)]
                consumed_cohorts.append({"source":c.get("source"),"period":c.get("period"),"provenance":prov,"units":take,"board_ids":taken_ids})
                if ids: c["board_ids"]=ids[take_i:]
                c["units"]-=take; remain-=take
                if c["units"]<=1e-9: s.s1_usable_cohorts.pop(0)
            if remain>1e-9: raise RuntimeError("S1 FIFO cohort conservation failure during production")
            # Mirror aggregate provenance counters for audit/readiness compatibility.
            s.s1_clean_boards-=consumed["clean"]; s.s1_latent_defect_boards-=consumed["latent"]
            s.s1_shortcut_reworked_boards-=consumed["shortcut"]; s.s1_full_reworked_boards-=consumed["full"]
            m.inventory["s1_boards"]=m.inventory.get("s1_boards",0)-use_s1
            for c in consumed_cohorts:
                s.finished_s1_cohorts.append(dict(c))
            s.finished_s1_clean+=consumed["clean"]; s.finished_s1_latent+=consumed["latent"]
            s.finished_s1_shortcut+=consumed["shortcut"]; s.finished_s1_full+=consumed["full"]
            m.inventory["kits"]-=n; m.inventory["finished"]=m.inventory.get("finished",0)+n; m.cash_k-=3*n
            util=max(n/max(1,self.available_pp(Role.M,"assembly")),n/max(1,self.available_pp(Role.M,"test")))
            s.m_overload_weeks = s.m_overload_weeks+1 if util>.90 else 0
            if s.m_overload_weeks>=2:
                m.pp["assembly"]=max(0,m.pp["assembly"]-5); m.pp["test"]=max(0,m.pp["test"]-5); s.m_overload_weeks=0
            self.world.ledger.append(s.period,"production",units=n,s1_boards=use_s1,s2_boards=use_s2,cash_cost_k=3*n)
        elif action.kind is ActionKind.SHIP and action.actor is Role.M:
            n=int(action.params.get("units",0)); n=min(n,int(m.inventory.get("finished",0)))
            need_slots=ceil(n/20) if n>0 else 0
            # Consume previously accepted M-C transport reservations for this period.
            remaining=need_slots; consumed=[]
            for r in getattr(s,"transport_reservations",[]):
                if remaining<=0: break
                if int(r.get("period",-1))!=s.period or r.get("route","M-C")!="M-C" or int(r.get("slots",0))<=0: continue
                take=min(remaining,int(r["slots"])); r["slots"]-=take; remaining-=take
                consumed.append((r.get("reservation_id"),r.get("mode"),take))
            s.transport_reservations=[r for r in s.transport_reservations if int(r.get("slots",0))>0 or int(r.get("period",-1))>s.period]
            m.inventory["finished"]-=n
            remain=float(n); shipped_risk={"ordinary":[],"shortcut":[],"full":[]}
            shipped_cohorts=[]
            while remain>1e-9 and s.finished_s1_cohorts:
                c=s.finished_s1_cohorts[0]; take=min(remain,float(c["units"])); take_i=int(take)
                prov=c["provenance"]
                ids=list(c.get("board_ids",[]))
                taken_ids=ids[:take_i] if ids else [f"{c.get('source','legacy')}:board:{i}" for i in range(take_i)]
                shipped_cohorts.append({"source":c.get("source"),"period":c.get("period"),"provenance":prov,"units":take,"board_ids":taken_ids})
                if prov=="latent": shipped_risk["ordinary"].extend(taken_ids); s.finished_s1_latent-=take
                elif prov=="shortcut": shipped_risk["shortcut"].extend(taken_ids); s.finished_s1_shortcut-=take
                elif prov=="full": shipped_risk["full"].extend(taken_ids); s.finished_s1_full-=take
                else: s.finished_s1_clean-=take
                if ids: c["board_ids"]=ids[take_i:]
                c["units"]-=take; remain-=take
                if c["units"]<=1e-9: s.finished_s1_cohorts.pop(0)
            # Residual finished units, if any, are S2-origin and carry no S1 field risk.
            # T execution is reliability-conditioned. A failed realization delays the intact
            # finished-goods shipment by exactly one benchmark period; there is no reroll.
            p=self.world.transport_reliability(s.transport_state)
            on_time=self.world.rng.uniform01("finished_transport",s.period,Role.M.value,Role.C.value) < p
            shipment_id=f"TR-{s.period}-M-C-{action.action_id}"
            if on_time:
                s.customer_reserve+=n
                s.pending_receipts.append({"due":s.period+1,"amount_k":7*n,"units":n})
                self.world.schedule_delivered_board_failures(shipment_id,shipped_risk)
                risk_counts={k:len(v) for k,v in shipped_risk.items()}
                self.world.ledger.append(s.period,"customer_delivery",shipment_id=shipment_id,units=n,receipt_due=s.period+1,transport_state=s.transport_state,on_time=True,slots=need_slots,reservations=tuple(consumed),risk_provenance=risk_counts,risk_board_ids={k:tuple(v) for k,v in shipped_risk.items()})
            else:
                s.pending_transport.append({"shipment_id":shipment_id,"due":s.period+1,"supplier":None,"customer":Role.C.value,"units":n,"price_k":0.0,"inventory_key":None,"receipt_k":7*n,"risk_provenance":{k:len(v) for k,v in shipped_risk.items()},"risk_board_ids":{k:list(v) for k,v in shipped_risk.items()}})
                self.world.ledger.append(s.period,"transport_delay",shipment_id=shipment_id,supplier=Role.M.value,customer=Role.C.value,units=n,transport_state=s.transport_state,due=s.period+1,delay_periods=1,slots=need_slots,reservations=tuple(consumed))
        elif action.kind is ActionKind.SHIP and action.actor in (Role.S1,Role.S2):
            supplier=action.actor; n=int(action.params.get("units",0)); price=2.0 if supplier is Role.S1 else 2.6
            inv_key="s1_boards" if supplier is Role.S1 else "s2_boards"
            stock_used=0
            if supplier is Role.S1:
                # Current line output is embedded in S1-SHIP; finished stock covers only the
                # amount above current line capability, preserving the frozen stock-buffer role.
                line=int(max(0,s.agents[Role.S1].pp.get("line",0)))
                stock_used=max(0,n-line)
                s.agents[Role.S1].inventory["stock"]=max(0,float(s.agents[Role.S1].inventory.get("stock",0))-stock_used)
            shipment_id=f"TR-{s.period}-{supplier.value}-M"
            shipment_quality_pp=float(s.agents[Role.S1].pp.get("quality",0.0)) if supplier is Role.S1 else None
            on_time=self.world.supplier_transport_on_time(supplier)
            if on_time:
                cost=price*n; m.cash_k-=cost; s.agents[supplier].cash_k+=cost
                if supplier is Role.S1: self._receive_s1_boards(shipment_id,n,shipment_quality_pp=shipment_quality_pp)
                else: m.inventory[inv_key]=m.inventory.get(inv_key,0)+n
                self.world.ledger.append(s.period,f"{supplier.value.lower()}_supply_arrival",shipment_id=shipment_id,units=n,stock_used=stock_used,cash_paid_k=cost,controller_action=True,transport_state=s.transport_state,on_time=True,shipment_quality_pp=shipment_quality_pp)
            else:
                s.pending_transport.append({"shipment_id":shipment_id,"due":s.period+1,"supplier":supplier.value,"units":n,"price_k":price,"inventory_key":inv_key,"shipment_quality_pp":shipment_quality_pp})
                self.world.ledger.append(s.period,"transport_delay",shipment_id=shipment_id,supplier=supplier.value,units=n,stock_used=stock_used,transport_state=s.transport_state,due=s.period+1,delay_periods=1)
        elif action.kind in (ActionKind.INSPECT,ActionKind.ENHANCED_INSPECT,ActionKind.FULL_CONTAINMENT):
            rate={ActionKind.INSPECT:.20,ActionKind.ENHANCED_INSPECT:.50,ActionKind.FULL_CONTAINMENT:1.0}[action.kind]
            s.current_s1_inspection_rate=rate
            self.world.ledger.append(s.period,"inspection",rate=rate)
        elif action.kind is ActionKind.M_CONSERVE:
            self.world.ledger.append(s.period,"m_conserve",production_cap=int(action.params.get("production_cap",0)))
        elif action.kind is ActionKind.M_RATION:
            self.world.ledger.append(s.period,"m_ration",customer_allocation=int(action.params.get("customer_allocation",0)))
        elif action.kind is ActionKind.M_SPLIT_SOURCE:
            self.world.ledger.append(s.period,"m_split_source",s1_units=int(action.params.get("s1_units",0)),s2_units=int(action.params.get("s2_units",0)))
        elif action.kind is ActionKind.M_BOOK_T:
            mode=str(action.params.get("mode")); slots=int(action.params.get("slots",0)); period=int(action.params.get("period",s.period)); fee=(4 if mode=="normal" else 12)*slots
            m.cash_k-=fee
            rid=f"TRES-{s.period}-{mode}-{period}-{len(s.transport_reservations)}"
            s.transport_reservations.append({"reservation_id":rid,"mode":mode,"period":period,"slots":slots,"route":action.params.get("route","M-C")})
            self.world.ledger.append(s.period,"transport_booking",reservation_id=rid,mode=mode,slots=slots,target_period=period,cash_cost_k=fee)
        elif action.kind is ActionKind.M_AMEND_L:
            m.cash_k-=30; s.m_covenant_headroom=min(1.0,s.m_covenant_headroom+.20); s.m_weekly_debt_burden_k+=10
            self.world.ledger.append(s.period,"emergency_amendment",fee_k=30,headroom=s.m_covenant_headroom,weekly_burden_k=s.m_weekly_debt_burden_k)
        elif action.kind is ActionKind.M_RECOVER_PP:
            domain=str(action.params.get("domain")); gain=10 if domain=="assembly" else 12
            m.cash_k-=25; m.encumbered["engineering"]=m.encumbered.get("engineering",0)+20
            s.pending_m_pp_recovery.append({"domain":domain,"gain":gain,"due":s.period})
            self.world.ledger.append(s.period,"m_pp_recovery_started",domain=domain,cash_cost_k=25,engineering=20,gain=gain)
        elif action.kind is ActionKind.M_PAUSE:
            if m.pp.get("test",0)<100 and self.available_pp(Role.M,"engineering")>=10:
                m.encumbered["engineering"]=m.encumbered.get("engineering",0)+10
                s.pending_m_pp_recovery.append({"domain":"test","gain":8,"due":s.period,"source":"quality_containment_pause"})
            self.world.ledger.append(s.period,"m_pause",line="AM-40")
        elif action.kind is ActionKind.M_BREACH_CONTROLLED:
            self.world.ledger.append(s.period,"controlled_breach",quantity_not_delivered=int(action.params.get("quantity_not_delivered",0)))
        elif action.kind is ActionKind.M_SHUT_LINE:
            s.m_line_shutdown=True
            self.world.ledger.append(s.period,"m_line_shutdown",line="AM-40",irreversible=True)
        elif action.kind is ActionKind.S1_ASSIST:
            m.cash_k-=20; m.encumbered["engineering"]=m.encumbered.get("engineering",0)+20
            s.s1_assisted_recovery=True; self.world.ledger.append(s.period,"s1_assistance",cash_cost_k=20,engineering=20)
        elif action.kind is ActionKind.START_S2_QUAL:
            self.world.start_s2_qualification(bool(action.params.get("emergency",False)))
            cid=f"COM-S2-QUAL-{s.period}"
            s.commitments[cid]=Commitment(cid,(Role.M,Role.S2),"s2_qualification",None,s.period,None,True,{"emergency":bool(action.params.get("emergency",False))})
        elif action.kind is ActionKind.S2_QUAL_STAGE:
            active=[c for c in s.commitments.values() if c.active and c.family=="s2_qualification" and Role.S2 in c.parties]
            emergency=bool(active[-1].metadata.get("emergency",False)) if active else bool(action.params.get("emergency",False))
            m=s.agents[Role.M]; s2=s.agents[Role.S2]
            m.cash_k-=20
            m.encumbered["engineering"]=m.encumbered.get("engineering",0)+20
            s2.encumbered["engineering"]=s2.encumbered.get("engineering",0)+20
            s2.encumbered["line"]=s2.encumbered.get("line",0)+20
            if emergency: m.encumbered["test"]=m.encumbered.get("test",0)+10
            passed=self.world.sample_s2_qualification_stage(emergency)
            self.world.ledger.append(s.period,"s2_qualification_stage_action",action_id=action.action_id,passed=passed,emergency=emergency,cash_cost_k=20,m_engineering=20,s2_engineering=20,m_test=10 if emergency else 0)
        elif action.kind is ActionKind.RESERVE_S2:
            cap=60.0; start=s.period+1; end=s.period+5; m.cash_k-=20; s.agents[Role.S2].cash_k+=20; s.s2_reserved_capacity=cap; s.s2_reservation_until=end
            cid=f"COM-S2-RES-{s.period}"; s.commitments[cid]=Commitment(cid,(Role.M,Role.S2),"s2_capacity",cap,start,end,True,{"fee_k":20,"nonrefundable":True})
            self.world.ledger.append(s.period,"s2_capacity_reserved",capacity=cap,start=start,end=end,cash_cost_k=20)
        elif action.kind is ActionKind.REQUEST_RENEGOTIATION:
            q=int(action.params.get("delivery",action.params.get("quantity",80)))
            s.current_customer_commitment=q
            self.world.ledger.append(s.period,"renegotiation_accepted",delivery=q,reduction=80-q,reserve_before=s.customer_reserve)
        elif action.kind is ActionKind.ORDER_S1:
            q=int(action.params.get("quantity",0)); start=s.period+1; cid=f"COM-S1-ORDER-{s.period}"
            s.commitments[cid]=Commitment(cid,(Role.M,Role.S1),"s1_order",q,start,start,True,{"price_k":2.0,"payment":"receipt"})
            self.world.ledger.append(s.period,"s1_order_accepted",quantity=q,delivery_period=start,price_k=2.0)
        elif action.kind is ActionKind.ORDER_S2:
            q=int(action.params.get("quantity",0)); start=s.period+1; cid=f"COM-S2-ORDER-{s.period}"
            s.commitments[cid]=Commitment(cid,(Role.M,Role.S2),"s2_order",q,start,start,True,{"price_k":2.6,"payment":"receipt"})
            self.world.ledger.append(s.period,"s2_order_accepted",quantity=q,delivery_period=start,price_k=2.6)
        elif action.kind is ActionKind.CANCEL:
            cid=str(action.params.get("commitment_id")); c=s.commitments[cid]
            s.commitments[cid]=Commitment(c.commitment_id,c.parties,c.family,c.quantity,c.start_period,c.end_period,False,c.metadata)
            if c.family=="s2_capacity":
                s.s2_reserved_capacity=0.0; s.s2_reservation_until=None
            self.world.ledger.append(s.period,"commitment_cancelled",commitment_id=cid,commitment_family=c.family,refund_k=0)
        elif action.kind is ActionKind.SHORTCUT_REWORK:
            n=int(action.params.get("units",20)); batches=ceil(n/20); m.cash_k-=25*batches; m.encumbered["test"]=m.encumbered.get("test",0)+10*batches
            board_ids=list(getattr(s,"s1_suspect_board_ids",[])[:n])
            if len(board_ids)<n:
                # Compatibility only for legacy fixtures that set the aggregate suspect counter directly.
                board_ids.extend(f"LEGACY-SUSPECT:{action.action_id}:{i}" for i in range(len(board_ids),n))
            s.s1_suspect_board_ids=list(getattr(s,"s1_suspect_board_ids",[])[n:])
            s.s1_suspect_boards-=n; s.s1_shortcut_reworked_boards+=n
            s.s1_usable_cohorts.append({"source":action.action_id,"period":s.period,"provenance":"shortcut","units":float(n),"board_ids":board_ids})
            m.inventory["s1_boards"]=m.inventory.get("s1_boards",0)+n
            self.world.ledger.append(s.period,"rework_batch",batch=action.action_id,units=n,full=False,substrate_consumed=n,board_ids=tuple(board_ids),field_risk_deferred_until_delivery=True)
        elif action.kind is ActionKind.FULL_REWORK:
            n=int(action.params.get("units",20)); batches=ceil(n/20); m.cash_k-=35*batches; m.encumbered["test"]=m.encumbered.get("test",0)+15*batches
            board_ids=list(getattr(s,"s1_suspect_board_ids",[])[:n])
            if len(board_ids)<n:
                board_ids.extend(f"LEGACY-SUSPECT:{action.action_id}:{i}" for i in range(len(board_ids),n))
            s.s1_suspect_board_ids=list(getattr(s,"s1_suspect_board_ids",[])[n:])
            s.s1_suspect_boards-=n
            s.pending_full_rework.append({"due":s.period+1,"units":n,"batch":action.action_id,"board_ids":board_ids})
            self.world.ledger.append(s.period,"full_rework_started",units=n,due=s.period+1,board_ids=tuple(board_ids))
        elif action.kind is ActionKind.REQUEST_FINANCE:
            amount=float(action.params.get("amount_k",0))
            if s.m_covenant_headroom>=.45:
                m.cash_k+=amount; s.m_credit_available_k-=amount; s.m_covenant_headroom-=.06*(amount/100)
                cid=f"COM-LOAN-{s.period}-{int(amount)}"; s.commitments[cid]=Commitment(cid,(Role.M,Role.L),"loan",amount,s.period,None,True)
                self.world.ledger.append(s.period,"credit_draw",amount_k=amount,headroom=s.m_covenant_headroom)
            else:
                self.world.ledger.append(s.period,"credit_draw_rejected",amount_k=amount,headroom=s.m_covenant_headroom)
        elif action.kind is ActionKind.S1_RECOVER:
            s1=s.agents[Role.S1]; s1.cash_k-=40; s1.encumbered["recovery"]=s1.encumbered.get("recovery",0)+25
            assisted=bool(getattr(s,"s1_assisted_recovery",False))
            line_gain=20.0 if assisted else 15.0
            quality_gain=25.0 if assisted else 20.0
            s1.pp["line"]=min(100.0,float(s1.pp.get("line",0))+line_gain); s1.pp["quality"]=min(100.0,float(s1.pp.get("quality",0))+quality_gain)
            s.s1_recovery_active=True
            if bool(getattr(s,"s1_containment_active",False)) and float(s1.pp.get("quality",0))>=35:
                s.s1_containment_active=False
                s.__dict__["s1_forced_closure_weeks"]=0
                self.world.ledger.append(s.period,"s1_containment_released",quality=float(s1.pp.get("quality",0)))
            # Assistance applies to the jointly accepted recovery transformation; it does not
            # remain as a hidden permanent multiplier on later independent recovery actions.
            s.s1_assisted_recovery=False
            self.world.ledger.append(s.period,"s1_recovery",cash_cost_k=40,recovery_pp=25,assisted=assisted,line_gain=line_gain,quality_gain=quality_gain,line=s1.pp["line"],quality=s1.pp["quality"])
        elif action.kind is ActionKind.S1_CONTAIN:
            s.s1_containment_active=True
            self.world.ledger.append(s.period,"s1_containment",quality=float(s.agents[Role.S1].pp.get("quality",0)),shipment_blocked=True)
        elif action.kind is ActionKind.M_RECOVERY_AGREEMENT:
            nxt=int(action.params.get("projected_next",0)); following=int(action.params.get("projected_following",0)); duration=int(action.params.get("duration_periods",0))
            if nxt>=70 and following>=80 and duration==2:
                e=Evidence(f"E-RECOVERY-C-{s.period}",s.period,Role.M,Role.C,"accepted_recovery_agreement",
                           {"projected_next":nxt,"projected_following":following,"accepted_period":s.period,"expires_after_period":s.period+1},EvidenceStatus.REPORTED,False)
                s.evidence.append(e)
                # v0.15: this benchmark permits one accepted recovery agreement per customer
                # relationship.  The flag prevents serial renewal after the two-decision window.
                s.__dict__["recovery_agreement_used"]=True
                self.world.ledger.append(s.period,"recovery_agreement_accepted",projected_next=nxt,projected_following=following,expires_after_period=s.period+1,one_time=True)
        elif action.kind is ActionKind.C_THREATEN:
            self.world.ledger.append(s.period,"customer_threat",reserve=s.customer_reserve)
        elif action.kind is ActionKind.C_CONTINUE:
            self.world.ledger.append(s.period,"customer_continue",reserve=s.customer_reserve)
        elif action.kind is ActionKind.C_TERMINATE:
            s.customer_terminated=True; self.world.ledger.append(s.period,"customer_termination",reserve=s.customer_reserve,controller_action=True)
        elif action.kind is ActionKind.L_APPROVE_DRAW:
            self.world.ledger.append(s.period,"lender_approve_draw",headroom=s.m_covenant_headroom)
        elif action.kind is ActionKind.L_REJECT_DRAW:
            self.world.ledger.append(s.period,"lender_reject_draw",headroom=s.m_covenant_headroom)
        elif action.kind is ActionKind.L_OFFER_AMEND:
            self.world.ledger.append(s.period,"lender_offer_amend",headroom=s.m_covenant_headroom)
        elif action.kind is ActionKind.L_REJECT_AMEND:
            self.world.ledger.append(s.period,"lender_reject_amend",headroom=s.m_covenant_headroom)
        elif action.kind is ActionKind.L_RESTRICT:
            self.world.ledger.append(s.period,"lender_restrict",headroom=s.m_covenant_headroom)
        elif action.kind is ActionKind.T_ACCEPT_BOOK:
            self.world.ledger.append(s.period,"transport_accept_booking",transport_state=s.transport_state)
        elif action.kind is ActionKind.T_REJECT_BOOK:
            self.world.ledger.append(s.period,"transport_reject_booking",transport_state=s.transport_state)
        elif action.kind is ActionKind.T_EXECUTE:
            self.world.ledger.append(s.period,"transport_execute",transport_state=s.transport_state,pending=len(s.pending_transport))
        elif action.kind in (ActionKind.S1_ACCEPT_ASSIST,ActionKind.S2_ACCEPT_QUAL,ActionKind.S2_ACCEPT_RES,ActionKind.C_ACCEPT_RENEG,ActionKind.C_REJECT_RENEG):
            self.world.ledger.append(s.period,"role_specific_proposal_response",actor=action.actor.value,kind=action.kind.value,proposal_id=action.params.get("proposal_id"))
        elif action.kind is ActionKind.PROPOSE:
            self.world.ledger.append(s.period,"proposal",actor=action.actor.value,target=action.target.value if action.target else None)
        elif action.kind is ActionKind.ACCEPT:
            self.world.ledger.append(s.period,"acceptance",actor=action.actor.value)
        elif action.kind is ActionKind.REJECT:
            self.world.ledger.append(s.period,"rejection",actor=action.actor.value)
        elif action.kind is ActionKind.NO_ACTION:
            self.world.ledger.append(s.period,"no_action",actor=action.actor.value)

    @staticmethod
    def _s1_defect_probability(quality_pp: float) -> float:
        if quality_pp >= 80: return .01
        if quality_pp >= 60: return .04
        if quality_pp >= 45: return .10
        if quality_pp >= 35: return .20
        # Frozen authority blocks S1 shipment below 35; there is no licensed defect-probability band below it.
        raise ConformanceError("S1 shipment quality below 35 has no frozen defect-probability branch")

    @staticmethod
    def _inspection_sample_size(units: int, rate: float) -> int:
        if units <= 0: return 0
        if rate >= 1.0: return units
        # Outcome-blind integer closure: smallest integer sample that meets the frozen stated percentage.
        rate_count=ceil(rate*units)
        minimum=10 if rate >= .50 and units >= 10 else (5 if units >= 5 else units)
        return min(units,max(minimum,rate_count))

    def _receive_s1_boards(self, shipment_id: str, units: int, shipment_quality_pp: float | None=None):
        """D7-D9/D11-D12: stable board identity, event-keyed random inspection, frozen quality-at-shipment bands."""
        s=self.state; m=s.agents[Role.M]
        q=float(s.agents[Role.S1].pp.get("quality",0.0) if shipment_quality_pp is None else shipment_quality_pp)
        p_defect=self._s1_defect_probability(q)
        rate=float(getattr(s,"current_s1_inspection_rate",.20))
        sample_n=self._inspection_sample_size(units,rate)
        board_ids=[f"{shipment_id}:board:{i}" for i in range(units)]
        # Uniform sample without replacement: event-key each board to a stable random rank and take the first k.
        ranked=sorted(board_ids,key=lambda bid:self.world.rng.uniform01("s1_inspection_sample_rank",shipment_id,bid))
        sampled_ids=set(ranked[:sample_n])
        clean=latent=suspect=tp=fp=fn=tn=0; accepted_sequence=[]; suspect_ids=[]
        for i,board_id in enumerate(board_ids):
            defective=self.world.rng.uniform01("s1_latent_defect",shipment_id,board_id) < p_defect
            sampled=board_id in sampled_ids
            accepted_prov=None
            if sampled:
                if defective:
                    positive=self.world.rng.uniform01("s1_inspection_sensitivity",shipment_id,board_id) < .90
                    if positive: suspect+=1; tp+=1; suspect_ids.append(board_id)
                    else: latent+=1; fn+=1; accepted_prov="latent"
                else:
                    false_positive=self.world.rng.uniform01("s1_inspection_specificity",shipment_id,board_id) >= .99
                    if false_positive: suspect+=1; fp+=1; suspect_ids.append(board_id)
                    else: clean+=1; tn+=1; accepted_prov="clean"
            else:
                if defective: latent+=1; accepted_prov="latent"
                else: clean+=1; accepted_prov="clean"
            if accepted_prov is not None:
                if accepted_sequence and accepted_sequence[-1]["provenance"]==accepted_prov:
                    accepted_sequence[-1]["units"]+=1.0; accepted_sequence[-1]["board_ids"].append(board_id)
                else:
                    accepted_sequence.append({"source":shipment_id,"period":s.period,"provenance":accepted_prov,"units":1.0,"board_ids":[board_id]})
        s.s1_clean_boards+=clean; s.s1_latent_defect_boards+=latent; s.s1_suspect_boards+=suspect
        s.s1_suspect_board_ids.extend(suspect_ids)
        s.s1_usable_cohorts.extend(accepted_sequence)
        m.inventory["s1_boards"]=m.inventory.get("s1_boards",0)+clean+latent
        self.world.ledger.append(s.period,"s1_incoming_quality",shipment_id=shipment_id,units=units,quality_pp=q,defect_probability=p_defect,inspection_rate=rate,sample_size=sample_n,sampled_board_ids=tuple(sorted(sampled_ids)),clean=clean,latent_escaped=latent,suspect=suspect,true_positive=tp,false_positive=fp,false_negative=fn,true_negative=tn,fifo_cohorts=len(accepted_sequence))

    def _process_due(self):
        s=self.state; m=s.agents[Role.M]
        due=[x for x in s.pending_receipts if x["due"]<=s.period]
        for x in due: m.cash_k+=x["amount_k"]; self.world.ledger.append(s.period,"customer_receipt",**x)
        s.pending_receipts=[x for x in s.pending_receipts if x["due"]>s.period]
        tr=[x for x in s.pending_transport if x["due"]<=s.period]
        for x in tr:
            n=int(x["units"])
            if x.get("customer")==Role.C.value:
                s.customer_reserve+=n
                receipt=float(x.get("receipt_k",7*n)); s.pending_receipts.append({"due":s.period+1,"amount_k":receipt,"units":n})
                risk_board_ids={k:list(v) for k,v in x.get("risk_board_ids",{}).items()}
                self.world.schedule_delivered_board_failures(x["shipment_id"],risk_board_ids)
                self.world.ledger.append(s.period,"customer_delivery",shipment_id=x["shipment_id"],units=n,receipt_due=s.period+1,controller_action=True,on_time=False,delayed_from=x["due"]-1,risk_provenance={k:len(v) for k,v in risk_board_ids.items()},risk_board_ids={k:tuple(v) for k,v in risk_board_ids.items()})
            else:
                supplier=Role(x["supplier"]); cost=float(x["price_k"])*n
                m.cash_k-=cost; s.agents[supplier].cash_k+=cost
                if supplier is Role.S1: self._receive_s1_boards(x["shipment_id"],n,shipment_quality_pp=x.get("shipment_quality_pp"))
                else: m.inventory[x["inventory_key"]]=m.inventory.get(x["inventory_key"],0)+n
                self.world.ledger.append(s.period,f"{supplier.value.lower()}_supply_arrival",shipment_id=x["shipment_id"],units=n,cash_paid_k=cost,controller_action=True,on_time=False,delayed_from=x["due"]-1)
        s.pending_transport=[x for x in s.pending_transport if x["due"]>s.period]
        rw=[x for x in s.pending_full_rework if x["due"]<=s.period]
        for x in rw:
            m.inventory["s1_boards"]=m.inventory.get("s1_boards",0)+x["units"]
            s.s1_full_reworked_boards+=x["units"]
            s.s1_usable_cohorts.append({"source":x["batch"],"period":s.period,"provenance":"full","units":float(x["units"]),"board_ids":list(x.get("board_ids",[]))})
            self.world.ledger.append(s.period,"full_rework_completed",units=x["units"],batch=x["batch"],field_risk_deferred_until_delivery=True)
        s.pending_full_rework=[x for x in s.pending_full_rework if x["due"]>s.period]
        failures=[q for q in s.field_failure_queue if q["due"]<=s.period]
        if failures:
            for q in failures:
                e=Evidence(f"E-FIELD-{s.period}-{q.get('board_id',q.get('batch'))}",s.period,"FIELD","ALL","field_failure",dict(q),EvidenceStatus.VERIFIED,True)
                s.evidence.append(e)
                s.observed_field_failures.append(dict(q,observed_period=s.period))
            # D10: evaluate attributable failures by rolling two-period DELIVERY cohort, not by due period.
            delivery_periods=sorted({int(q["delivery_period"]) for q in s.observed_field_failures})
            candidate_window_ends=sorted({d for d in delivery_periods} | {d+1 for d in delivery_periods})
            triggered=set(int(x) for x in s.major_field_windows_triggered)
            for window_end in candidate_window_ends:
                if window_end in triggered: continue
                members=[q for q in s.observed_field_failures if int(q["delivery_period"]) in (window_end-1,window_end)]
                if len(members)>=4:
                    m.pp["test"]=max(0,m.pp["test"]-15); s.m_covenant_headroom-=.20; s.major_field_events+=1; s.customer_quality_pressure+=1
                    s.major_field_windows_triggered.append(window_end); triggered.add(window_end)
                    self.world.ledger.append(s.period,"major_field_quality_event",failures=len(members),delivery_window=(window_end-1,window_end),failure_board_ids=tuple(q.get("board_id") for q in members),test_pp=m.pp["test"],headroom=s.m_covenant_headroom)
        s.field_failure_queue=[q for q in s.field_failure_queue if q["due"]>s.period]

    def _customer_period_end(self):
        s=self.state
        delivered=sum(e.payload.get("units",0) for e in self.world.ledger.entries if e.period==s.period and e.family=="customer_delivery")
        commitment=int(getattr(s,"current_customer_commitment",80))
        missing=max(0,commitment-delivered)
        s.customer_reserve=max(0,s.customer_reserve-80)
        if s.customer_reserve<=0: s.agents[Role.C].pp["operations"]=max(0,s.agents[Role.C].pp["operations"]-10)
        strikes=2 if missing>50 else (1 if missing>20 else 0)
        if strikes: s.breach_strikes.extend([s.period]*strikes); s.m_covenant_headroom-=.10 if any(p==s.period-1 for p in s.breach_strikes) else 0
        if delivered>=76: s.consecutive_good_delivery_weeks+=1
        else: s.consecutive_good_delivery_weeks=0
        s.breach_strikes=[p for p in s.breach_strikes if p>=s.period-4]
        # Frozen v0.4 semantics: the world establishes termination eligibility; C decides whether
        # to exercise the irreversible exit. Eligibility itself must never auto-terminate the relationship.
        s.customer_termination_eligible = len(s.breach_strikes)>=4
        self.world.ledger.append(s.period,"customer_period_end",delivered=delivered,commitment=commitment,missing=missing,reserve=s.customer_reserve,strikes=len(s.breach_strikes),termination_eligible=s.customer_termination_eligible,terminated=s.customer_terminated)
        s.current_customer_commitment=80

    def _apply_period_end_pp_recovery(self):
        s=self.state; m=s.agents[Role.M]
        due=[x for x in getattr(s,"pending_m_pp_recovery",[]) if int(x.get("due",s.period))<=s.period]
        for x in due:
            d=str(x["domain"]); before=float(m.pp.get(d,0)); m.pp[d]=min(100.0,before+float(x["gain"]))
            self.world.ledger.append(s.period,"m_pp_recovery_completed",domain=d,before=before,after=m.pp[d],gain=float(x["gain"]),source=x.get("source","engineering_recovery"))
        s.pending_m_pp_recovery=[x for x in getattr(s,"pending_m_pp_recovery",[]) if x not in due]

    def _period_end_finance(self):
        s=self.state; m=s.agents[Role.M]
        m.cash_k-=80+s.m_weekly_debt_burden_k
        if m.cash_k<-100: s.m_covenant_headroom-=.08
        self.world.ledger.append(s.period,"fixed_overhead",cash_k=m.cash_k,headroom=s.m_covenant_headroom)

    def realize(self, actions: Iterable[Action], advance: bool=True) -> TransitionResult:
        resolution=self.resolve_joint(actions)
        before_e=len(self.state.evidence)
        phase={
            ActionKind.REQUEST_FINANCE:10, ActionKind.M_AMEND_L:10, ActionKind.M_BOOK_T:18, ActionKind.S1_ASSIST:20, ActionKind.START_S2_QUAL:20, ActionKind.S2_QUAL_STAGE:25,
            ActionKind.M_RECOVER_PP:28, ActionKind.M_PAUSE:32, ActionKind.M_CONSERVE:38, ActionKind.M_SPLIT_SOURCE:38, ActionKind.M_RATION:45, ActionKind.M_BREACH_CONTROLLED:45, ActionKind.M_SHUT_LINE:52,
            ActionKind.RESERVE_S2:20, ActionKind.INSPECT:30, ActionKind.ENHANCED_INSPECT:30,
            ActionKind.FULL_CONTAINMENT:30, ActionKind.SHORTCUT_REWORK:35, ActionKind.FULL_REWORK:35,
            ActionKind.ROUTINE_PRODUCE:40, ActionKind.SHIP:50, ActionKind.REQUEST_RENEGOTIATION:60, ActionKind.M_RECOVERY_AGREEMENT:60,
            ActionKind.ORDER_S1:60, ActionKind.ORDER_S2:60, ActionKind.CANCEL:15, ActionKind.S1_RECOVER:22,
            ActionKind.C_THREATEN:55, ActionKind.C_CONTINUE:55, ActionKind.C_TERMINATE:55,
            ActionKind.L_APPROVE_DRAW:12, ActionKind.L_REJECT_DRAW:12, ActionKind.L_OFFER_AMEND:12, ActionKind.L_REJECT_AMEND:12, ActionKind.L_RESTRICT:12,
            ActionKind.T_ACCEPT_BOOK:45, ActionKind.T_REJECT_BOOK:45, ActionKind.T_EXECUTE:48,
            ActionKind.PROPOSE:60, ActionKind.ACCEPT:60, ActionKind.REJECT:60, ActionKind.NO_ACTION:90,
        }
        for a in sorted(resolution.accepted,key=lambda x:(phase.get(x.kind,50),x.action_id)): self._execute(a)
        self._customer_period_end(); self._apply_period_end_pp_recovery(); self._period_end_finance()
        if advance:
            # Temporary encumbrances release only when the period closes.
            for agent in self.state.agents.values(): agent.encumbered.clear()
            self.world.advance_period(); self._process_due()
        return TransitionResult(deepcopy(self.state),resolution.accepted,resolution.rejected,tuple(self.state.evidence[before_e:]))
