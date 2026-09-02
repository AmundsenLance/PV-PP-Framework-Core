from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from math import ceil
from statistics import mean
from time import perf_counter
from typing import Iterable

from .model import Action, ActionKind, Packet, PacketKind, Role, Evidence, EvidenceStatus
from .world import AsterionWorld
from .engine import AsterionTransitionEngine
from .planning import ProjectionBudget, PlanningBudgetExceeded, BudgetCounter, DecisionTrace
from .controllers import Candidate, SigmaSelector, ScalarEstimator, BASE_B_WEIGHTS, LOCAL_PRIORITIES
from .scenario import MultiAgentScenarioRunner, ScenarioSnapshot
from .rng import SemanticRNG
from .outcomes import reconstruct_outcomes


@dataclass(frozen=True)
class ProductionProjection:
    action: Action
    path_losses: tuple[dict[str,float], ...]
    governing: tuple[float,...]
    all_domain: tuple[float,...]
    valid: bool
    adequate: bool
    irreversible_critical_damage: bool


@dataclass(frozen=True)
class ProductionDecision:
    trace: DecisionTrace
    projected: tuple[ProductionProjection,...]
    objective_score: float | None = None
    actions: tuple[Action,...] = ()


@dataclass(frozen=True)
class PrimaryRunRecord:
    regime: str
    seed: int
    deterministic: bool
    through_period: int
    history: tuple[ScenarioSnapshot,...]
    decision_traces: tuple[DecisionTrace,...]
    terminal: bool
    final_customer_reserve: float
    final_m_cash_k: float
    final_s1_line: float
    final_s1_quality: float
    s2_qualified: bool
    r_emergency_active: bool
    major_field_events: int
    ledger_entries: int
    outcomes: dict[str,object] = field(default_factory=dict)


def _transport_slot_caps(state: str) -> tuple[int,int]:
    return {"LOW":(6,2),"MEDIUM":(4,2),"HIGH":(3,1)}[str(state).upper()]

def _transport_state_for_period(period: int) -> str:
    if period < 5: return "LOW"
    if period < 9: return "MEDIUM"
    if period < 12: return "HIGH"
    return "MEDIUM"


def _m_root_actions(packet: Packet) -> tuple[Action,...]:
    """Full current-period M root lattice licensed by the frozen benchmark fixture.

    Integer-valued physical families enumerate every state-feasible integer value.  The
    production runner later composes the selected internal action with the common routine
    flow; bilateral actions remain proposals requiring explicit counterpart acceptance.
    """
    if packet.kind is not PacketKind.PRE or packet.role is not Role.M:
        raise ValueError("production M root actions require an M PRE packet")
    p=packet.period; obs=packet.direct_observations
    mpp=obs.get("own_pp",{}); inv=obs.get("inventory",{}); cash=float(obs.get("cash_k",0))
    s1=int(max(0,inv.get("s1_boards",0))); s2=int(max(0,inv.get("s2_boards",0))) if bool(obs.get("s2_qualified",False)) else 0
    max_prod=int(max(0,min(s1+s2,inv.get("kits",0),mpp.get("assembly",0),mpp.get("test",0),max(0,cash)//3)))
    max_prod=min(100,max_prod)
    routine=min(80,max_prod)
    actions=[]
    def add(kind, params=None, target=None, tag=None):
        actions.append(Action(f"M-{p}-{tag or kind.value}-{len(actions):05d}",Role.M,kind,params or {},target))

    add(ActionKind.NO_ACTION)
    add(ActionKind.INSPECT,{"rate":.20})
    add(ActionKind.ENHANCED_INSPECT,{"rate":.50})
    add(ActionKind.FULL_CONTAINMENT,{"rate":1.0})

    # v0.11 CLOSED physical/internal M families. Every integer point is exposed.
    for cap in range(0,max_prod+1): add(ActionKind.M_CONSERVE,{"production_cap":cap},tag=f"conserve-{cap}")
    max_alloc=int(min(80,inv.get("finished",0)+routine))
    for q in range(0,max_alloc+1): add(ActionKind.M_RATION,{"customer_allocation":q},tag=f"ration-{q}")
    # Split-source is one internal production allocation. Lower totals remain licensed and
    # therefore naturally overlap conservation; no coarse source-share grid is introduced.
    for q1 in range(0,min(s1,max_prod)+1):
        q2max=min(s2,max_prod-q1)
        for q2 in range(0,q2max+1):
            add(ActionKind.M_SPLIT_SOURCE,{"s1_units":q1,"s2_units":q2},tag=f"split-{q1}-{q2}")

    horizon=int(obs.get("benchmark_end_period",16))
    for period in range(p,horizon+1):
        normal_cap,exp_cap=_transport_slot_caps(_transport_state_for_period(period))
        for mode,cap in (("normal",normal_cap),("expedite",exp_cap)):
            for slots in range(1,cap+1):
                add(ActionKind.M_BOOK_T,{"mode":mode,"route":"M-C","period":period,"slots":slots},Role.T,f"book-{mode}-{period}-{slots}")

    headroom=float(obs.get("m_covenant_headroom",1.0))
    if headroom < .25 and cash>=30:
        add(ActionKind.M_AMEND_L,{"kind":"emergency","fee_k":30},Role.L,"amend-emergency")
    if cash>=25 and float(mpp.get("engineering",0))>=20:
        if float(mpp.get("assembly",0))<100: add(ActionKind.M_RECOVER_PP,{"domain":"assembly"},tag="recover-assembly")
        if float(mpp.get("test",0))<100: add(ActionKind.M_RECOVER_PP,{"domain":"test"},tag="recover-test")

    # v0.4 already defines these three transformations. They were not among the seven v0.11
    # closure rows; their provenance is retained explicitly in the M6 audit/lock record.
    add(ActionKind.M_PAUSE,{"line":"AM-40"},tag="pause")
    for miss in range(1,81): add(ActionKind.M_BREACH_CONTROLLED,{"quantity_not_delivered":miss},tag=f"breach-{miss}")
    add(ActionKind.M_SHUT_LINE,{"line":"AM-40"},tag="shutdown")

    add(ActionKind.S1_ASSIST,{"cash_k":20,"engineering":20},Role.S1)
    add(ActionKind.START_S2_QUAL,{"emergency":False},Role.S2)
    if any(e.claim_family=="emergency_qualification_notice" and e.authoritative for e in packet.evidence):
        add(ActionKind.START_S2_QUAL,{"emergency":True},Role.S2,"qual-em")
    add(ActionKind.RESERVE_S2,{"capacity":60,"duration":5,"cash_k":20},Role.S2)
    suspect=int(float(obs.get("s1_suspect_boards",0)))
    for units in (20,40):
        if units<=suspect:
            add(ActionKind.SHORTCUT_REWORK,{"units":units},tag=f"shortcut-{units}")
            add(ActionKind.FULL_REWORK,{"units":units},tag=f"full-{units}")
    for amount in range(50,501,50): add(ActionKind.REQUEST_FINANCE,{"amount_k":amount},Role.L,f"finance-{amount}")
    for q in range(60,81): add(ActionKind.REQUEST_RENEGOTIATION,{"delivery":q},Role.C,f"reneg-{q}")
    for q in range(0,91): add(ActionKind.ORDER_S1,{"quantity":q},Role.S1,f"s1order-{q}")
    if bool(obs.get("s2_qualified",False)):
        cap=max(0,70-int(obs.get("s2_external_encumbrance",0)))
        if bool(obs.get("s2_conditional",False)): cap=min(40,cap)
        for q in range(0,cap+1): add(ActionKind.ORDER_S2,{"quantity":q},Role.S2,f"s2order-{q}")
    for c in packet.commitments:
        if c.active and c.start_period>p and c.family in ("s2_capacity","s1_order","s2_order","s2_qualification"):
            add(ActionKind.CANCEL,{"commitment_id":c.commitment_id},tag=f"cancel-{c.commitment_id}")
    return tuple(actions)


def _routine_flow_from_packet(packet: Packet, intervention: Action | None=None) -> tuple[Action,...]:
    if packet.role is not Role.M: return ()
    obs=packet.direct_observations; inv=obs.get("inventory",{}); pp=obs.get("own_pp",{}); cash=float(obs.get("cash_k",0))
    feasible=int(max(0,min(80,inv.get("s1_boards",0)+inv.get("s2_boards",0),inv.get("kits",0),pp.get("assembly",0),pp.get("test",0),max(0,cash)//3)))
    n=feasible; ship_cap=80; prod_params={"units":n}
    k=intervention.kind if intervention is not None else None
    if k is ActionKind.M_CONSERVE:
        n=min(feasible,int(intervention.params.get("production_cap",feasible))); prod_params={"units":n}
    elif k is ActionKind.M_SPLIT_SOURCE:
        q1=int(intervention.params.get("s1_units",0)); q2=int(intervention.params.get("s2_units",0)); n=q1+q2
        prod_params={"units":n,"s1_units":q1,"s2_units":q2}
    elif k is ActionKind.M_RATION:
        ship_cap=int(intervention.params.get("customer_allocation",80))
    elif k is ActionKind.M_PAUSE:
        n=0; prod_params={"units":0}
    elif k is ActionKind.M_BREACH_CONTROLLED:
        miss=max(0,min(80,int(intervention.params.get("quantity_not_delivered",0))))
        target=80-miss; n=min(feasible,target); ship_cap=target; prod_params={"units":n}
    elif k is ActionKind.M_SHUT_LINE:
        n=0; prod_params={"units":0}
    out=[]
    if n: out.append(Action(f"FLOW-{packet.period}-PROD",Role.M,ActionKind.ROUTINE_PRODUCE,prod_params))
    finished=int(inv.get("finished",0))+n; q=int(min(ship_cap,finished))
    if q: out.append(Action(f"FLOW-{packet.period}-SHIP",Role.M,ActionKind.SHIP,{"units":q},Role.C))
    return tuple(out)

def _visible_s1(packet: Packet, estimator: ScalarEstimator | None=None) -> tuple[float,float,float]:
    line=90.0; quality=90.0; uncertainty=20.0
    if estimator is not None:
        if "S1.line" in estimator.beliefs: line=estimator.beliefs["S1.line"].value; uncertainty=estimator.beliefs["S1.line"].uncertainty
        if "S1.quality" in estimator.beliefs: quality=estimator.beliefs["S1.quality"].value; uncertainty=max(uncertainty,estimator.beliefs["S1.quality"].uncertainty)
    else:
        for e in packet.evidence:
            if e.claim_family=="supplier_status" and e.payload.get("mode")=="exact":
                line=float(e.payload.get("line",line)); quality=float(e.payload.get("quality",quality)); uncertainty=4.0
    return line,quality,uncertainty



def _credible_recovery_terms(packet: Packet) -> dict[str,int] | None:
    """Two-period non-oracle delivery projection for the v0.14 customer recovery contract.

    Uses only M PRE-visible state and the already-frozen public production/supply model.  It is a
    plan, not a guarantee: transport realization remains stochastic and no resources are created.
    """
    if packet.role is not Role.M or packet.kind is not PacketKind.PRE:
        return None
    obs=packet.direct_observations; inv=obs.get("inventory",{}); pp=obs.get("own_pp",{})
    cash=max(0.0,float(obs.get("cash_k",0))); assembly=float(pp.get("assembly",0)); test=float(pp.get("test",0))
    boards=float(inv.get("s1_boards",0))+float(inv.get("s2_boards",0)); kits=float(inv.get("kits",0)); finished=float(inv.get("finished",0))
    line,quality,_=_visible_s1(packet,None)
    # Next period: accessible finished goods plus production from already accessible inputs.
    prod1=max(0.0,min(80.0,boards,kits,assembly,test,cash//3)); next_delivery=int(min(80.0,finished+prod1))
    boards=max(0.0,boards-prod1); kits=max(0.0,kits-prod1); cash=max(0.0,cash-3*prod1)
    # Frozen finance model: receipts from the projected next delivery arrive one period later;
    # include the ordinary weekly fixed overhead before assessing following-period production.
    cash=max(0.0,cash + 7*next_delivery - 80.0)
    # Following period: public model permits one ordinary S1 supply cycle and 95 kits.
    boards += max(0.0,min(90.0,line)); kits += 95.0
    prod2=max(0.0,min(80.0,boards,kits,assembly,test,cash//3)); following_delivery=int(min(80.0,prod2))
    if next_delivery>=70 and following_delivery>=80:
        return {"projected_next":next_delivery,"projected_following":following_delivery,"duration_periods":2}
    return None

def _path_loss(packet: Packet, action: Action, path_index: int, seed: int,
               estimator: ScalarEstimator | None, counter: BudgetCounter) -> dict[str,float]:
    """Frozen four-transition public-interface projection using only PRE-visible state.

    Randomness is semantic-keyed by (seed, period, action family, path, step). It samples the
    frozen deterioration and transport families without revealing future realized primary draws.
    """
    cash=float(packet.direct_observations.get("cash_k",0)); inv=packet.direct_observations.get("inventory",{})
    boards=float(inv.get("s1_boards",0))+float(inv.get("s2_boards",0)); kits=float(inv.get("kits",0))
    pp=packet.direct_observations.get("own_pp",{}); assembly=float(pp.get("assembly",0)); test=float(pp.get("test",0))
    reserve=float(packet.direct_observations.get("customer_reserve",120)); line,quality,unc=_visible_s1(packet,estimator)
    rng=SemanticRNG(seed)
    L={"commitment":0.0,"shortage":0.0,"cash":0.0,"capability":0.0,"quality":0.0,"adaptation":0.0,"recovery":0.0}
    critical=False
    current_prod_cap=80.0; current_delivery_cap=80.0
    # Current-period intervention effects only; future consequences follow public transition model.
    if action.kind is ActionKind.S1_ASSIST: cash-=20; L["adaptation"]+=.20; line=min(100,line+15); quality=min(100,quality+20); L["recovery"]-=.18
    elif action.kind is ActionKind.START_S2_QUAL: cash-=35; L["adaptation"]+=.35; L["capability"]+=.15
    elif action.kind is ActionKind.RESERVE_S2: cash-=20; L["adaptation"]+=.20; L["recovery"]-=.12
    elif action.kind is ActionKind.SHORTCUT_REWORK: cash-=25*ceil(float(action.params.get("units",20))/20); L["adaptation"]+=.18; L["quality"]+=.20
    elif action.kind is ActionKind.FULL_REWORK: cash-=35*ceil(float(action.params.get("units",20))/20); L["adaptation"]+=.25; L["quality"]+=.04
    elif action.kind is ActionKind.ENHANCED_INSPECT: L["adaptation"]+=.10; L["quality"]-=.06
    elif action.kind is ActionKind.FULL_CONTAINMENT: L["adaptation"]+=.20; L["quality"]-=.12
    elif action.kind is ActionKind.REQUEST_FINANCE: L["adaptation"]+=.05; cash+=float(action.params.get("amount_k",0))
    elif action.kind is ActionKind.REQUEST_RENEGOTIATION: L["adaptation"]+=.04
    elif action.kind in (ActionKind.ORDER_S1,ActionKind.ORDER_S2): L["adaptation"]+=.02
    elif action.kind is ActionKind.CANCEL: L["adaptation"]+=.03
    elif action.kind is ActionKind.M_CONSERVE:
        current_prod_cap=float(action.params.get("production_cap",80)); L["adaptation"]+=.01
    elif action.kind is ActionKind.M_RATION:
        current_delivery_cap=float(action.params.get("customer_allocation",80)); L["adaptation"]+=.01
    elif action.kind is ActionKind.M_SPLIT_SOURCE:
        current_prod_cap=float(action.params.get("s1_units",0))+float(action.params.get("s2_units",0)); L["adaptation"]+=.01
    elif action.kind is ActionKind.M_BOOK_T:
        mode=str(action.params.get("mode","normal")); slots=float(action.params.get("slots",1)); cash-=(4 if mode=="normal" else 12)*slots; L["adaptation"]+=.03
    elif action.kind is ActionKind.M_AMEND_L:
        cash-=30; L["adaptation"]+=.12; L["cash"]-=.10; L["recovery"]-=.08
    elif action.kind is ActionKind.M_RECOVER_PP:
        cash-=25; L["adaptation"]+=.08
        if action.params.get("domain")=="assembly": assembly=min(100,assembly+10)
        else: test=min(100,test+12)
        L["capability"]-=.08
    elif action.kind is ActionKind.M_PAUSE:
        current_prod_cap=0; L["adaptation"]+=.08; test=min(100,test+8)
    elif action.kind is ActionKind.M_BREACH_CONTROLLED:
        miss=float(action.params.get("quantity_not_delivered",0)); current_prod_cap=max(0,80-miss); current_delivery_cap=max(0,80-miss); L["adaptation"]+=.04
    elif action.kind is ActionKind.M_SHUT_LINE:
        current_prod_cap=0; current_delivery_cap=0; L["recovery"]+=4.0; critical=True

    for step in range(4):
        counter.consume()
        # Uncertain deterioration draw around frozen untreated increments; estimator uncertainty
        # broadens projection but does not access actual primary future draws.
        if line<85 or quality<85:
            sev=rng.choice([-.25,0,.25],[.25,.5,.25],"prod_proj_sev",packet.period,action.kind.value,path_index,step)
            line=max(0,line-(8*(1+sev))); quality=max(0,quality-(10*(1+sev)))
        # Transport success affects effective delivered quantity.
        tstate="LOW" if packet.period+step<5 else ("MEDIUM" if packet.period+step<9 else "HIGH")
        tprob={"LOW":.96,"MEDIUM":.90,"HIGH":.82}[tstate]
        supply=min(90.0,line)
        boards+=supply; kits+=95
        step_cap=current_prod_cap if step==0 else 80.0
        produce=min(step_cap,boards,kits,assembly,test,max(0,cash)//3)
        boards-=produce; kits-=produce; cash-=3*produce
        success=rng.uniform01("prod_proj_transport",packet.period,action.kind.value,path_index,step) < tprob
        delivered=produce if success else .75*produce
        if step==0: delivered=min(delivered,current_delivery_cap)
        target=float(action.params.get("delivery",80)) if action.kind is ActionKind.REQUEST_RENEGOTIATION and step==0 else 80.0
        miss=max(0,target-delivered)
        L["shortage"]+=miss/80; L["commitment"]+=miss/80
        reserve=max(0,reserve+delivered-80)
        cash+=7*delivered-80
        if quality<70: L["quality"]+=(70-quality)/70*.20
        if line<70: L["recovery"]+=(70-line)/70*.25
        if cash<0: L["cash"]+=min(2.0,abs(cash)/100)
        if reserve<=0: L["recovery"]+=2.0; critical=True
    if critical: L["recovery"]+=2.0
    return {k:max(0.0,v) for k,v in L.items()}


def _aggregate_projection(action: Action, losses: tuple[dict[str,float],...], valid: bool=True) -> ProductionProjection:
    avg={k:mean(x[k] for x in losses) for k in losses[0]}
    critical=sum(1 for x in losses if x["recovery"]>=2.0) > len(losses)/2
    governing=(avg["commitment"],avg["shortage"],avg["recovery"])
    alld=tuple(avg[k] for k in ("commitment","shortage","cash","capability","quality","adaptation","recovery"))
    adequate=valid and avg["recovery"]<2.0 and avg["cash"]<1.0
    return ProductionProjection(action,losses,governing,alld,valid,adequate,critical)


def _cvar90(scores: list[float]) -> float:
    if not scores: return 0.0
    s=sorted(scores); n=max(1,ceil(.10*len(s))); return mean(s[-n:])


class ProductionPVPPControllerA:
    """Primary A controller: explicit structural selection with Sigma, no scalar final score."""
    def __init__(self,budget:ProjectionBudget|None=None,projection_paths:int|None=None):
        self.budget=budget or ProjectionBudget(); self.paths=projection_paths or self.budget.projection_paths; self.sigma=SigmaSelector()
    def decide(self,packet:Packet,seed:int) -> ProductionDecision:
        if packet.kind is not PacketKind.PRE or packet.role is not Role.M: raise ValueError("A production controller requires M PRE")
        counter=BudgetCounter(self.budget); projections=[]; exhausted=False
        actions=_m_root_actions(packet)
        paths_per_action=max(1,min(self.paths,self.budget.projection_paths,self.budget.transition_evaluations//max(1,len(actions)*self.budget.horizon)))
        for a in actions:
            path_losses=[]
            try:
                for j in range(paths_per_action): path_losses.append(_path_loss(packet,a,j,seed,None,counter))
            except PlanningBudgetExceeded:
                exhausted=True; break
            projections.append(_aggregate_projection(a,tuple(path_losses)))
        if not projections:
            chosen=next(a for a in actions if a.kind is ActionKind.NO_ACTION)
        else:
            cs=[Candidate(x.action.action_id,x.valid,x.adequate,x.governing,x.all_domain,x.irreversible_critical_damage) for x in projections]
            sel=self.sigma.select(cs); chosen=next((x.action for x in projections if sel and x.action.action_id==sel.policy_id),projections[0].action)
        trace=DecisionTrace("A-PRODUCTION",Role.M,packet.period,chosen,len(actions),len(projections),counter.evaluations,counter.elapsed,exhausted,("SEARCH_BUDGET_EXHAUSTED",) if exhausted else ())
        return ProductionDecision(trace,tuple(projections),None,_routine_flow_from_packet(packet,chosen)+(chosen,))


class ProductionScalarControllerB:
    """Primary B controller implementing frozen 75% expected + 25% CVaR90 objective."""
    def __init__(self,budget:ProjectionBudget|None=None,panel:str="B0",projection_paths:int|None=None):
        self.budget=budget or ProjectionBudget(); self.paths=projection_paths or self.budget.projection_paths; self.panel=panel; self.estimator=ScalarEstimator()
    def _weights(self)->dict[str,float]:
        w=dict(BASE_B_WEIGHTS[Role.M])
        if self.panel=="B1":
            for k in ("commitment","shortage"): w[k]*=1.25
            w["adaptation"]*=.8; w["cash"]*=.9
        elif self.panel=="B2":
            for k in ("capability","quality","recovery"): w[k]*=1.25
            w["adaptation"]*=.8; w["commitment"]*=.9
        elif self.panel=="B3": w["cash"]*=1.35; w["adaptation"]*=1.15; w["commitment"]*=.9
        elif self.panel=="B4": w["quality"]*=1.5; w["commitment"]*=.85; w["adaptation"]*=.9
        z=sum(w.values()); return {k:v/z for k,v in w.items()}
    def decide(self,packet:Packet,seed:int)->ProductionDecision:
        if packet.kind is not PacketKind.PRE or packet.role is not Role.M: raise ValueError("B production controller requires M PRE")
        self.estimator.absorb(packet); counter=BudgetCounter(self.budget); actions=_m_root_actions(packet); projections=[]; scored=[]; exhausted=False; w=self._weights()
        paths_per_action=max(1,min(self.paths,self.budget.projection_paths,self.budget.transition_evaluations//max(1,len(actions)*self.budget.horizon)))
        for a in actions:
            path_losses=[]
            try:
                for j in range(paths_per_action): path_losses.append(_path_loss(packet,a,j,seed,self.estimator,counter))
            except PlanningBudgetExceeded:
                exhausted=True; break
            pr=_aggregate_projection(a,tuple(path_losses)); projections.append(pr)
            ps=[sum(w.get(k,0)*v for k,v in L.items()) for L in path_losses]
            score=.75*mean(ps)+.25*_cvar90(ps)
            scored.append((score,a.action_id,a))
        chosen=min(scored,key=lambda x:(x[0],x[1]))[2] if scored else next(a for a in actions if a.kind is ActionKind.NO_ACTION)
        objective=min(scored)[0] if scored else None
        self.estimator.propagate_freshness(1)
        trace=DecisionTrace(f"B-{self.panel}-PRODUCTION",Role.M,packet.period,chosen,len(actions),len(projections),counter.evaluations,counter.elapsed,exhausted,("SEARCH_BUDGET_EXHAUSTED",) if exhausted else ())
        return ProductionDecision(trace,tuple(projections),objective,_routine_flow_from_packet(packet,chosen)+(chosen,))


class ProductionLocalControllerC:
    """Primary C controller: current/local ordered priorities with four-period recent summary only."""
    def __init__(self): self.recent=[]
    def decide(self,packet:Packet,seed:int=0)->ProductionDecision:
        if packet.kind is not PacketKind.PRE or packet.role is not Role.M: raise ValueError("C production controller requires M PRE")
        actions=_m_root_actions(packet); reserve=float(packet.direct_observations.get("customer_reserve",120)); cash=float(packet.direct_observations.get("cash_k",0))
        exact=[]
        for e in packet.evidence:
            if e.claim_family=="supplier_status" and e.payload.get("mode")=="exact": exact.append((float(e.payload.get("line",100)),float(e.payload.get("quality",100))))
        # Ordered current/local reaction; no recovery-corridor optimization.
        preferred=[]
        if exact and min(exact[-1])<70:
            preferred=[ActionKind.FULL_CONTAINMENT,ActionKind.S1_ASSIST,ActionKind.START_S2_QUAL]
        elif reserve<60:
            preferred=[ActionKind.REQUEST_RENEGOTIATION,ActionKind.S1_ASSIST,ActionKind.REQUEST_FINANCE]
        elif cash<100:
            preferred=[ActionKind.REQUEST_FINANCE]
        else:
            preferred=[ActionKind.INSPECT,ActionKind.NO_ACTION]
        chosen=None
        for k in preferred:
            candidates=[a for a in actions if a.kind is k]
            if candidates:
                # For finance choose smallest draw; renegotiation choose smallest commitment reduction.
                if k is ActionKind.REQUEST_FINANCE: chosen=min(candidates,key=lambda a:a.params.get("amount_k",0))
                elif k is ActionKind.REQUEST_RENEGOTIATION: chosen=max(candidates,key=lambda a:a.params.get("delivery",0))
                else: chosen=candidates[0]
                break
        if chosen is None: chosen=next(a for a in actions if a.kind is ActionKind.NO_ACTION)
        self.recent.append((packet.period,reserve,cash)); self.recent=self.recent[-4:]
        trace=DecisionTrace("C-PRODUCTION",Role.M,packet.period,chosen,len(actions),1,0,0.0,False,("LOCAL_CURRENT_RULE",))
        return ProductionDecision(trace,(),None,_routine_flow_from_packet(packet,chosen)+(chosen,))


def _routine_flow_actions(world:AsterionWorld, regime:str) -> list[Action]:
    """Common controller-neutral operating baseline.

    The benchmark's comparison concerns adaptive intervention architecture; routine feasible
    production and shipment are common physical operations and do not receive regime identity.
    """
    s=world.state; m=s.agents[Role.M]; eng=AsterionTransitionEngine(world)
    boards=m.inventory.get("s1_boards",0)+m.inventory.get("s2_boards",0); kits=m.inventory.get("kits",0)
    cap=min(eng.available_pp(Role.M,"assembly"),eng.available_pp(Role.M,"test")); cash=max(0,m.cash_k)//3
    n=int(max(0,min(80,boards,kits,cap,cash)))
    out=[]
    if n: out.append(Action(f"FLOW-{s.period}-PROD",Role.M,ActionKind.ROUTINE_PRODUCE,{"units":n}))
    finished=int(m.inventory.get("finished",0))+n
    q=int(min(80,finished))
    if q: out.append(Action(f"FLOW-{s.period}-SHIP",Role.M,ActionKind.SHIP,{"units":q},Role.C))
    return out


class PrimaryProductionRunner:
    """Production-grade single-regime Asterion runner.

    A/B/C see the same PRE packet and common world/action surface. The runner never exposes
    ORACLE state and never compares regimes internally. Cross-regime pairing is external.
    """
    def __init__(self,regime:str,seed:int,deterministic:bool=False,budget:ProjectionBudget|None=None):
        self.regime=regime; self.seed=seed; self.deterministic=deterministic; self.world=AsterionWorld(seed)
        self.scenario=MultiAgentScenarioRunner(self.world,deterministic=deterministic)
        if regime=="A": self.controller=ProductionPVPPControllerA(budget)
        elif regime.startswith("B"):
            panel=regime if regime in {"B0","B1","B2","B3","B4"} else "B0"; self.controller=ProductionScalarControllerB(budget,panel)
        elif regime=="C": self.controller=ProductionLocalControllerC()
        else: raise ValueError(f"unknown regime {regime}")
        self.traces=[]
    def _set_stochastic_fixture(self):
        if self.deterministic: return
        s=self.world.state
        if s.period==0 and not hasattr(s,"stochastic_primary_onset"):
            rng=SemanticRNG(self.seed)
            s.stochastic_primary_onset=rng.choice([3,4,5],[1/3,1/3,1/3],"s1_onset",0)
            dec=rng.choice([(10,15),(15,20),(20,25)],[.25,.5,.25],"s1_initial_severity",0)
            s.stochastic_initial_dec=dec
        # Scenario runner reads these if present (patched below).
    def step(self):
        self._set_stochastic_fixture(); p=self.world.state.period; packet=self.world.packet(Role.M)
        d=self.controller.decide(packet,self.seed)
        self.traces.append(d.trace)
        actions=list(d.actions)
        return self.scenario.step(actions)
    def run(self,through_period:int=16)->PrimaryRunRecord:
        while self.world.state.period<=through_period and not self.world.state.customer_terminated:
            self.step()
        s=self.world.state
        return PrimaryRunRecord(self.regime,self.seed,self.deterministic,through_period,tuple(self.scenario.history),tuple(self.traces),s.customer_terminated,s.customer_reserve,s.agents[Role.M].cash_k,s.agents[Role.S1].pp.get("line",0),s.agents[Role.S1].pp.get("quality",0),s.s2_qualified,s.r_emergency_active,getattr(s,"major_field_events",0),len(self.world.ledger.entries))

class ProductionRolePolicy:
    """V2 role-specific controller implementation over the common PRE action surface.

    This milestone implements only action families whose world transformation is numerically
    specified by pre-run authority. It is deliberately not a hidden counterpart policy: each
    role chooses from its own legitimate packet. A/B/C use different selection architectures.
    """
    def __init__(self,regime:str,role:Role):
        self.regime=regime; self.role=role; self.state={}

    def _noop(self,p:int):
        return Action(f"{self.regime}-{self.role.value}-{p}-noop",self.role,ActionKind.NO_ACTION)

    def _s1_candidates(self,packet:Packet) -> list[Action]:
        p=packet.period; obs=packet.direct_observations; pp=obs.get("own_pp",{}); cash=float(obs.get("cash_k",0))
        line=float(pp.get("line",0)); quality=float(pp.get("quality",0)); recovery=float(pp.get("recovery",0))
        out=[self._noop(p)]
        contained=bool(obs.get("s1_containment_active",False))
        if quality<35 and not contained:
            out.append(Action(f"{self.regime}-S1-{p}-contain",Role.S1,ActionKind.S1_CONTAIN,{},Role.S1))
        live=[c for c in packet.commitments if c.active and c.start_period<=p and (c.end_period is None or c.end_period>=p) and c.family in ("board_supply","s1_order")]
        if live and not contained and quality>=35:
            # v0.13 embeds current-period board production in shipment. Accessible finished stock
            # supplements, rather than replaces, current line capability.
            stock=float(obs.get("inventory",{}).get("stock",0))
            q=int(max(0,min(float(live[-1].quantity or 0),line+stock)))
            if q>0: out.append(Action(f"{self.regime}-S1-{p}-ship",Role.S1,ActionKind.SHIP,{"units":q},Role.M))
        if cash>=40 and recovery>=25 and (line<90 or quality<90):
            out.append(Action(f"{self.regime}-S1-{p}-recover",Role.S1,ActionKind.S1_RECOVER,{},Role.S1))
        return out

    def _choose_s1(self,packet:Packet,cands:list[Action]) -> Action:
        obs=packet.direct_observations; pp=obs.get("own_pp",{}); line=float(pp.get("line",0)); quality=float(pp.get("quality",0))
        ship=next((a for a in cands if a.kind is ActionKind.SHIP),None); rec=next((a for a in cands if a.kind is ActionKind.S1_RECOVER),None); contain=next((a for a in cands if a.kind is ActionKind.S1_CONTAIN),None)
        # Below the frozen observed-quality boundary, containment is mandatory for every architecture.
        if contain is not None: return contain
        if self.regime=="A":
            # PV-PP role frame: preserve a live recovery corridor when line/quality enter the
            # critical band; otherwise honor the accepted shipment commitment.
            if rec is not None and (line<70 or quality<70): return rec
            if ship is not None: return ship
            return rec or cands[0]
        if self.regime.startswith("B"):
            # Frozen B0 S1 dimensions: fulfillment, cash, line, quality, recovery expenditure,
            # irreversible exit. Compare current feasible actions with a transparent scalar proxy.
            w=BASE_B_WEIGHTS[Role.S1]
            scored=[]
            for a in cands:
                fulfillment=0.0; cash=0.0; line_loss=max(0,70-line)/70; quality_loss=max(0,70-quality)/70; recovery_cost=0.0; exit=0.0
                if a.kind is ActionKind.SHIP:
                    q=float(a.params.get("units",0)); fulfillment=max(0,90-q)/90
                elif a.kind is ActionKind.S1_RECOVER:
                    fulfillment=1.0 if ship is not None else 0.0; cash=40/260; recovery_cost=40/260
                    line_loss=max(0,70-min(100,line+15))/70; quality_loss=max(0,70-min(100,quality+20))/70
                else:
                    fulfillment=1.0 if ship is not None else 0.0
                score=w["fulfillment"]*fulfillment+w["cash"]*cash+w["line"]*line_loss+w["quality"]*quality_loss+w["recovery_cost"]*recovery_cost+w["exit"]*exit
                scored.append((score,a.action_id,a))
            return min(scored,key=lambda x:(x[0],x[1]))[2]
        # C local priority: safety block first, then current accepted shipment, then capability.
        if quality<35 and rec is not None: return rec
        if ship is not None: return ship
        return rec or cands[0]

    def _choose_s2(self,packet:Packet) -> Action:
        p=packet.period; obs=packet.direct_observations; line=float(obs.get("own_pp",{}).get("line",0))
        active_qual=[c for c in packet.commitments if c.active and c.family=="s2_qualification"]
        if active_qual and line>=20:
            return Action(f"{self.regime}-S2-{p}-qual-stage",Role.S2,ActionKind.S2_QUAL_STAGE,{},Role.M)
        live=[c for c in packet.commitments if c.active and c.start_period<=p and (c.end_period is None or c.end_period>=p) and c.family=="s2_order"]
        if live and bool(obs.get("s2_qualified",False)):
            cap=line-float(obs.get("s2_external_encumbrance",0));
            if bool(obs.get("s2_conditional",False)): cap=min(40,cap)
            q=int(max(0,min(float(live[-1].quantity or 0),cap)))
            if q>0: return Action(f"{self.regime}-S2-{p}-ship",Role.S2,ActionKind.SHIP,{"units":q},Role.M)
        return self._noop(p)

    def _choose_customer(self,packet:Packet) -> Action:
        p=packet.period
        # M13 prospective cooperative-recovery calibration.  The Asterion world contains no
        # replacement supplier for C.  The rolling-strike state therefore denotes severe
        # relationship distress; it is not itself an economically viable exit trigger.
        #
        # C already carries an operations-PP state in the frozen world.  That PP falls by 10
        # at each period end in which reserve is exhausted.  No new numeric cutoff is introduced:
        # C exercises irreversible exit only after its pre-existing operations PP has collapsed
        # to zero, representing failure of C's own downstream business.  Until then C continues
        # working with M because the modeled outside sourcing option is zero.
        operations=float(packet.direct_observations.get("own_pp",{}).get("operations",100.0))
        kind=ActionKind.C_TERMINATE if operations<=0.0 else ActionKind.C_CONTINUE
        return Action(f"{self.regime}-C-{p}-{kind.value}",Role.C,kind,{},Role.M)

    def _choose_lender(self,packet:Packet) -> Action:
        p=packet.period; h=float(packet.direct_observations.get("m_covenant_headroom",1.0))
        if h<.25: kind=ActionKind.L_RESTRICT
        elif h<.45: kind=ActionKind.L_OFFER_AMEND
        else: kind=ActionKind.L_APPROVE_DRAW
        return Action(f"{self.regime}-L-{p}-{kind.value}",Role.L,kind,{},Role.M)

    def _choose_transport(self,packet:Packet) -> Action:
        p=packet.period; pending=int(packet.direct_observations.get("pending_transport",0))
        kind=ActionKind.T_EXECUTE if pending else ActionKind.T_ACCEPT_BOOK
        return Action(f"{self.regime}-T-{p}-{kind.value}",Role.T,kind,{},Role.M)

    def _live_proposal(self,packet:Packet):
        props=[e for e in packet.evidence if e.claim_family=="live_proposal" and e.status is not None]
        return props[-1] if props else None

    def _proposal_accept_feasible(self,packet:Packet,evidence) -> bool:
        k=ActionKind(evidence.payload["action_kind"]); params=dict(evidence.payload.get("params",{})); obs=packet.direct_observations
        if self.role is Role.C and k is ActionKind.REQUEST_RENEGOTIATION:
            q=float(params.get("delivery",params.get("quantity",80))); r=float(obs.get("customer_reserve",0))
            return not bool(obs.get("customer_terminated",False)) and 60<=q<=80 and max(0.0,r+q-80.0)>=40.0
        if self.role is Role.C and k is ActionKind.M_RECOVERY_AGREEMENT:
            return (not bool(obs.get("customer_terminated",False)) and
                    float(params.get("projected_next",0))>=70 and float(params.get("projected_following",0))>=80 and
                    int(params.get("duration_periods",0))==2)
        if self.role is Role.S1 and k is ActionKind.S1_ASSIST:
            # The proposal itself establishes M's offered assistance. S1 may accept while active;
            # M-side resource feasibility is independently validated at joint realization.
            return True
        if self.role is Role.S1 and k is ActionKind.ORDER_S1:
            q=float(params.get("quantity",0)); pp=obs.get("own_pp",{}); inv=obs.get("inventory",{})
            return 0<=q<=90 and q<=max(0.0,float(pp.get("line",0))+float(inv.get("stock",0)))
        if self.role is Role.S2 and k is ActionKind.ORDER_S2:
            q=float(params.get("quantity",0)); cap=max(0.0,float(obs.get("own_pp",{}).get("line",0))-float(obs.get("s2_external_encumbrance",0)))
            if bool(obs.get("s2_conditional",False)): cap=min(40.0,cap)
            return bool(obs.get("s2_qualified",False)) and 0<=q<=cap
        if self.role is Role.S2 and k is ActionKind.RESERVE_S2:
            return float(params.get("capacity",60))==60 and int(params.get("duration",5))==5 and max(0.0,float(obs.get("own_pp",{}).get("line",0))-float(obs.get("s2_external_encumbrance",0)))>=60
        if self.role is Role.S2 and k is ActionKind.START_S2_QUAL:
            return float(obs.get("own_pp",{}).get("engineering",0))>=20 and float(obs.get("own_pp",{}).get("line",0))>=20
        if self.role is Role.L and k is ActionKind.REQUEST_FINANCE:
            amount=float(params.get("amount_k",0)); return amount>0 and amount<=float(obs.get("m_credit_available_k",0)) and float(obs.get("m_covenant_headroom",0))>=.45
        if self.role is Role.L and k is ActionKind.M_AMEND_L:
            return float(obs.get("m_covenant_headroom",1.0))<.25
        if self.role is Role.T and k is ActionKind.M_BOOK_T:
            mode=str(params.get("mode","")); slots=int(params.get("slots",0)); period=int(params.get("period",packet.period))
            if mode not in ("normal","expedite") or slots<1: return False
            normal,exp=_transport_slot_caps(_transport_state_for_period(period)); cap=normal if mode=="normal" else exp
            used=sum(int(x.get("slots",0)) for x in obs.get("transport_reservations",()) if int(x.get("period",-1))==period and x.get("mode")==mode)
            return slots<=max(0,cap-used)
        return False

    def decide_bundle(self,packet:Packet,seed:int) -> tuple[DecisionTrace,tuple[Action,...]]:
        """Return controller trace plus up to one proposal response and one physical/internal action."""
        proposal=self._live_proposal(packet)
        physical=None
        # Compute physical/internal action from the same role controller.
        if self.role is Role.S1:
            cands=self._s1_candidates(packet); physical=self._choose_s1(packet,cands)
        elif self.role is Role.S2:
            physical=self._choose_s2(packet)
        elif self.role is Role.C:
            physical=self._choose_customer(packet)
        elif self.role is Role.L:
            physical=self._choose_lender(packet)
        elif self.role is Role.T:
            physical=self._choose_transport(packet)
        else:
            physical=self._noop(packet.period)
        actions=[]; primary=physical
        evaluated=1
        if proposal is not None:
            feasible=self._proposal_accept_feasible(packet,proposal)
            accept=feasible
            # V2 prospective S2 semantic closure: physical feasibility is not a duty to accept a
            # binding reservation. With a verified competing external buyer and no separately
            # frozen compensating premium, A/B preserve the outside option and reject the binding
            # 60x5 reservation; C follows its frozen local contract-before-opportunity priority.
            if feasible and self.role is Role.S2 and ActionKind(proposal.payload["action_kind"]) is ActionKind.RESERVE_S2:
                outside=any(e.claim_family=="external_market_opportunity" and e.status is EvidenceStatus.VERIFIED for e in packet.evidence)
                if outside and (self.regime=="A" or self.regime.startswith("B")):
                    accept=False
            pk=ActionKind(proposal.payload["action_kind"])
            if feasible and self.role is Role.L and pk is ActionKind.M_AMEND_L:
                h=float(packet.direct_observations.get("m_covenant_headroom",0)); mc=float(packet.direct_observations.get("m_cash_k",0))
                # Prospectively frozen role semantics: A evaluates preservation of the repayment
                # system, B0 is conservative about added exposure, and C takes the viable-workout
                # branch before restriction when the borrower is not already beyond recovery.
                if self.regime=="A": accept = mc > -100
                elif self.regime.startswith("B"): accept = False
                else: accept = mc > -100
            if accept:
                if self.role is Role.S1 and pk is ActionKind.S1_ASSIST: kind=ActionKind.S1_ACCEPT_ASSIST
                elif self.role is Role.S2 and pk is ActionKind.START_S2_QUAL: kind=ActionKind.S2_ACCEPT_QUAL
                elif self.role is Role.S2 and pk is ActionKind.RESERVE_S2: kind=ActionKind.S2_ACCEPT_RES
                elif self.role is Role.C and pk is ActionKind.REQUEST_RENEGOTIATION: kind=ActionKind.C_ACCEPT_RENEG
                elif self.role is Role.C and pk is ActionKind.M_RECOVERY_AGREEMENT: kind=ActionKind.ACCEPT
                elif self.role is Role.L and pk is ActionKind.REQUEST_FINANCE: kind=ActionKind.L_APPROVE_DRAW
                elif self.role is Role.L and pk is ActionKind.M_AMEND_L: kind=ActionKind.L_OFFER_AMEND
                elif self.role is Role.T and pk is ActionKind.M_BOOK_T: kind=ActionKind.T_ACCEPT_BOOK
                else: kind=ActionKind.ACCEPT
            else:
                if self.role is Role.C and pk is ActionKind.REQUEST_RENEGOTIATION: kind=ActionKind.C_REJECT_RENEG
                elif self.role is Role.L and pk is ActionKind.REQUEST_FINANCE: kind=ActionKind.L_REJECT_DRAW
                elif self.role is Role.L and pk is ActionKind.M_AMEND_L: kind=ActionKind.L_REJECT_AMEND
                elif self.role is Role.T and pk is ActionKind.M_BOOK_T: kind=ActionKind.T_REJECT_BOOK
                else: kind=ActionKind.REJECT
            resp=Action(f"{self.regime}-{self.role.value}-{packet.period}-{kind.value}-{proposal.evidence_id}",self.role,kind,{"proposal_id":proposal.evidence_id},Role.M)
            actions.append(resp); primary=resp; evaluated+=1
        if physical.kind is not ActionKind.NO_ACTION:
            actions.append(physical)
        if not actions: actions=[physical]
        architecture="PVPP" if self.regime=="A" else ("SCALAR" if self.regime.startswith("B") else "LOCAL")
        trace=DecisionTrace(f"{self.regime}-V2-{architecture}-{self.role.value}",self.role,packet.period,primary,len(packet.action_kinds),evaluated,0,0.0,False,("V2_ROLE_CONTROLLER",architecture,"EXPLICIT_PROPOSAL_RESPONSE" if proposal else "NO_PROPOSAL"))
        return trace,tuple(actions)

    def decide(self,packet:Packet,seed:int)->DecisionTrace:
        return self.decide_bundle(packet,seed)[0]


class HomogeneousPrimaryProductionRunner:
    """V2 homogeneous population runner under the prospective implementation annex.

    Each economic role receives its own legitimate PRE packet and a regime-specific controller.
    R remains an institutional rule process. Comparative execution remains separately gated.
    """
    ECONOMIC_ROLES=(Role.M,Role.S1,Role.S2,Role.C,Role.L,Role.T)
    def __init__(self,regime:str,seed:int,deterministic:bool=False,budget:ProjectionBudget|None=None):
        self.regime=regime; self.seed=seed; self.deterministic=deterministic; self.world=AsterionWorld(seed)
        self.engine=AsterionTransitionEngine(self.world)
        self.m_runner=PrimaryProductionRunner(regime,seed,deterministic,budget)
        # Reuse its production controller only, not its focal-M scenario/world.
        self.m_controller=self.m_runner.controller
        self.role_controllers={r:ProductionRolePolicy(regime,r) for r in self.ECONOMIC_ROLES if r is not Role.M}
        self.history=[]; self.traces=[]; self.state_history=[]
        s=self.world.state
        self._capture_state()
        s.__dict__.setdefault("s1_onset_period",3); s.__dict__.setdefault("s1_deterioration_active",False)
        s.__dict__.setdefault("s2_opportunity_announced",False); s.__dict__.setdefault("s2_opportunity_closed",False)
    def _capture_state(self):
        s=self.world.state
        self.state_history.append({
            "period":int(s.period), "m_cash_k":float(s.agents[Role.M].cash_k),
            "headroom":float(getattr(s,"m_covenant_headroom",1.0)),
            "customer_reserve":float(s.customer_reserve),
            "pp":{r.value:dict(a.pp) for r,a in s.agents.items()},
        })

    def _start_exogenous(self):
        s=self.world.state; p=s.period
        if not self.deterministic and p==0 and not hasattr(s,"stochastic_primary_onset"):
            rng=SemanticRNG(self.seed); s.stochastic_primary_onset=rng.choice([3,4,5],[1/3,1/3,1/3],"s1_onset",0); s.stochastic_initial_dec=rng.choice([(10,15),(15,20),(20,25)],[.25,.5,.25],"s1_initial_severity",0)
        onset=3 if self.deterministic else int(getattr(s,"stochastic_primary_onset",3)); initial=(15,20) if self.deterministic else tuple(getattr(s,"stochastic_initial_dec",(15,20)))
        if p==onset and not s.s1_deterioration_active: self.world.deteriorate_s1(p,*initial); s.s1_deterioration_active=True
        elif p>onset and s.s1_deterioration_active:
            dec=(8,10) if self.deterministic else self.world.rng.choice([(5,7),(8,10),(11,13)],[.25,.5,.25],"s1_untreated",p)
            self.world.deteriorate_s1(p,*dec)
        if s.s1_deterioration_active: self.world.s1_message(p)
        if p==6 and not s.s2_opportunity_announced: self.world.activate_s2_external_opportunity(); s.s2_opportunity_announced=True
        if p==5: s.transport_state="MEDIUM"
        if p==9: s.transport_state="HIGH"
        if p==12: s.transport_state="MEDIUM"
        if not s.r_emergency_active and s.s1_deterioration_active:
            line=float(s.agents[Role.S1].pp.get("line",0)); self.world.r_emergency_check((line,line),80.0,False)
    def _common_kit_arrival(self):
        m=self.world.state.agents[Role.M]; m.inventory["kits"]=m.inventory.get("kits",0)+95.0; self.world.ledger.append(self.world.state.period,"kit_supply_arrival",units=95.0)
    def step(self):
        self._start_exogenous(); s=self.world.state; p=s.period; self._common_kit_arrival()
        mp=self.world.packet(Role.M); md=self.m_controller.decide(mp,self.seed); self.traces.append(md.trace)
        selected=md.trace.action
        proposal_kinds={ActionKind.S1_ASSIST,ActionKind.START_S2_QUAL,ActionKind.RESERVE_S2,ActionKind.REQUEST_RENEGOTIATION,ActionKind.M_RECOVERY_AGREEMENT,ActionKind.ORDER_S1,ActionKind.ORDER_S2,ActionKind.REQUEST_FINANCE,ActionKind.M_AMEND_L,ActionKind.M_BOOK_T}
        proposal_evidence=None; proposal_evidences=[]; proposal_actions={}
        # Routine/physical M flow remains immediately submitted. Bilateral interaction actions are
        # converted to one-period proposal objects and execute only after matching ACCEPT.
        actions=[a for a in md.actions if a is not selected and a.action_id!=selected.action_id]
        if selected.kind in proposal_kinds and selected.target is not None:
            proposal_evidence=Evidence(f"PROP-{p}-{selected.action_id}",p,Role.M,selected.target,"live_proposal",
                {"proposal_action_id":selected.action_id,"action_kind":selected.kind.value,"params":dict(selected.params),"target":selected.target.value},EvidenceStatus.REPORTED,False)
            proposal_evidences.append(proposal_evidence); proposal_actions[proposal_evidence.evidence_id]=selected
        else:
            actions.append(selected)
        # v0.14 closes the previously unreachable customer-recovery corridor as the second
        # external proposal slot allowed by the frozen V2 slot rule.  It is common to A/B/C and
        # appears only at the actual termination boundary when M's PRE-visible two-period plan
        # satisfies the already-frozen 70/80 thresholds.
        terms=_credible_recovery_terms(mp)
        # v0.15 anti-rollover closure: the recovery corridor is a one-time two-decision
        # forbearance instrument for this benchmark relationship.  Once accepted, no fresh
        # recovery agreement may be issued later in the same run; expiry therefore returns C
        # to the ordinary termination rule rather than silently creating rolling protection.
        recovery_unused = not bool(getattr(s,"recovery_agreement_used",False))
        if recovery_unused and bool(mp.direct_observations.get("termination_eligible",False)) and float(mp.direct_observations.get("customer_reserve",120))<40 and terms is not None:
            ra=Action(f"M-{p}-recovery-agreement",Role.M,ActionKind.M_RECOVERY_AGREEMENT,terms,Role.C,2)
            re=Evidence(f"PROP-{p}-{ra.action_id}",p,Role.M,Role.C,"live_proposal",
                {"proposal_action_id":ra.action_id,"action_kind":ra.kind.value,"params":dict(ra.params),"target":Role.C.value},EvidenceStatus.REPORTED,False)
            proposal_evidences.append(re); proposal_actions[re.evidence_id]=ra
        for pe in proposal_evidences:
            s.evidence.append(pe); self.world.ledger.append(p,"proposal_issued",proposal_id=pe.evidence_id,action_id=proposal_actions[pe.evidence_id].action_id,action_kind=proposal_actions[pe.evidence_id].kind.value,target=pe.recipient.value if hasattr(pe.recipient,"value") else str(pe.recipient),terms=dict(proposal_actions[pe.evidence_id].params))
        accepted_ids=set()
        # Every economic role receives a sealed PRE packet and may issue both one proposal response
        # and one physical/internal action under the V2 slot rule.
        for r,c in self.role_controllers.items():
            tr,bundle=c.decide_bundle(self.world.packet(r),self.seed); self.traces.append(tr); actions.extend(bundle)
            accept_kinds={ActionKind.ACCEPT,ActionKind.S1_ACCEPT_ASSIST,ActionKind.S2_ACCEPT_QUAL,ActionKind.S2_ACCEPT_RES,ActionKind.C_ACCEPT_RENEG,ActionKind.L_APPROVE_DRAW,ActionKind.L_OFFER_AMEND,ActionKind.T_ACCEPT_BOOK}
            for pe in proposal_evidences:
                if pe.recipient is r and any(a.kind in accept_kinds and a.params.get("proposal_id")==pe.evidence_id for a in bundle): accepted_ids.add(pe.evidence_id)
        for pe in proposal_evidences:
            pa=proposal_actions[pe.evidence_id]
            if pe.evidence_id in accepted_ids:
                actions.append(pa); self.world.ledger.append(p,"proposal_matched_acceptance",proposal_id=pe.evidence_id,action_id=pa.action_id)
            else:
                self.world.ledger.append(p,"proposal_rejected_or_expired",proposal_id=pe.evidence_id,action_id=pa.action_id)
        # Realize current-period actions without advancing so end-P7 opportunity closure sees P7 actions.
        res=self.engine.realize(actions,advance=False)
        if proposal_evidences:
            ids={e.evidence_id for e in proposal_evidences}; s.evidence=[e for e in s.evidence if e.evidence_id not in ids]
        if p==7 and not s.s2_opportunity_closed:
            reservation_exists=bool(s.s2_reserved_capacity>0 and (s.s2_reservation_until is None or s.s2_reservation_until>=8))
            self.world.close_s2_opportunity_if_unreserved(reservation_exists); s.s2_opportunity_closed=True
        # Close period exactly as engine does after realization.
        for agent in s.agents.values(): agent.encumbered.clear()
        self.world.advance_period(); self.engine._process_due(); self._capture_state()
        snap=ScenarioSnapshot(s.period,s.customer_reserve,s.agents[Role.M].cash_k,s.agents[Role.S1].pp.get("line",0),s.agents[Role.S1].pp.get("quality",0),s.s2_qualified,s.s2_external_encumbrance,s.r_emergency_active,s.customer_terminated)
        self.history.append(snap); return res
    def run(self,through_period:int=16)->PrimaryRunRecord:
        while self.world.state.period<=through_period and not self.world.state.customer_terminated: self.step()
        s=self.world.state
        metrics=reconstruct_outcomes(self.world,self.traces,self.state_history).as_dict()
        return PrimaryRunRecord(self.regime,self.seed,self.deterministic,through_period,tuple(self.history),tuple(self.traces),s.customer_terminated,s.customer_reserve,s.agents[Role.M].cash_k,s.agents[Role.S1].pp.get("line",0),s.agents[Role.S1].pp.get("quality",0),s.s2_qualified,s.r_emergency_active,getattr(s,"major_field_events",0),len(self.world.ledger.entries),metrics)
