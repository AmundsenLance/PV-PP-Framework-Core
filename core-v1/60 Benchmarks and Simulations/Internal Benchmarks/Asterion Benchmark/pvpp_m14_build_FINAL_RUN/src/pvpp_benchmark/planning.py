from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from time import perf_counter
from typing import Callable, Iterable

from .model import Action, ActionKind, Packet, PacketKind, Role, WorldState
from .grammar import common_action_grammar
from .controllers import Candidate, SigmaSelector, ScalarEstimator, BASE_B_WEIGHTS


class PlanningBudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class ProjectionBudget:
    transition_evaluations: int = 10_000
    wall_clock_seconds: float = 2.0
    projection_paths: int = 256
    horizon: int = 4


@dataclass
class BudgetCounter:
    budget: ProjectionBudget
    started: float = field(default_factory=perf_counter)
    evaluations: int = 0

    def consume(self, n: int = 1) -> None:
        self.evaluations += n
        if self.evaluations > self.budget.transition_evaluations:
            raise PlanningBudgetExceeded("transition-evaluation ceiling exceeded")
        if perf_counter() - self.started > self.budget.wall_clock_seconds:
            raise PlanningBudgetExceeded("wall-clock ceiling exceeded")

    @property
    def elapsed(self) -> float:
        return perf_counter() - self.started


@dataclass(frozen=True)
class ProjectedOutcome:
    action: Action
    losses: dict[str, float]
    governing: tuple[float, ...]
    all_domain: tuple[float, ...]
    valid: bool = True
    adequate: bool = True
    irreversible_critical_damage: bool = False


@dataclass(frozen=True)
class DecisionTrace:
    controller: str
    role: Role
    period: int
    action: Action
    candidate_count: int
    evaluated_count: int
    transition_evaluations: int
    elapsed_seconds: float
    budget_exhausted: bool
    notes: tuple[str, ...] = ()


def default_action_candidates(packet: Packet) -> list[Action]:
    """Deterministic, common root-action instantiation for calibration fixtures.

    This is intentionally conservative: it instantiates one canonical root action per
    licensed action family. Parameter expansion for the full research simulator will
    be added only through frozen grammar tables.
    """
    if packet.kind is not PacketKind.PRE:
        raise ValueError("controllers accept PRE packets only")
    actions=[]
    for idx,kind in enumerate(common_action_grammar(packet.role)):
        params={}
        target=None
        if packet.role is Role.M:
            if kind is ActionKind.ROUTINE_PRODUCE: params={"units":80}
            elif kind is ActionKind.SHIP: params={"units":80}; target=Role.C
            elif kind is ActionKind.INSPECT: params={"rate":.20}
            elif kind is ActionKind.ENHANCED_INSPECT: params={"rate":.50}
            elif kind is ActionKind.FULL_CONTAINMENT: params={"rate":1.0}
            elif kind is ActionKind.S1_ASSIST: params={"cash_k":40,"recovery_pp":25}; target=Role.S1
            elif kind is ActionKind.START_S2_QUAL: params={"emergency":False}; target=Role.S2
            elif kind is ActionKind.RESERVE_S2: params={"capacity":60,"duration":5,"cash_k":20}; target=Role.S2
            elif kind is ActionKind.SHORTCUT_REWORK: params={"units":20}
            elif kind is ActionKind.FULL_REWORK: params={"units":20}
            elif kind is ActionKind.REQUEST_FINANCE: params={"amount_k":100}; target=Role.L
            elif kind is ActionKind.REQUEST_RENEGOTIATION: params={"delivery":60}; target=Role.C
            elif kind is ActionKind.ORDER_S1: params={"quantity":90}; target=Role.S1
            elif kind is ActionKind.ORDER_S2: params={"quantity":40}; target=Role.S2
            elif kind is ActionKind.CANCEL:
                future=[c for c in packet.commitments if c.active and c.start_period>packet.period and c.family in ("s2_capacity","s1_order","s2_order","s2_qualification")]
                params={"commitment_id":future[0].commitment_id if future else ""}
        actions.append(Action(f"{packet.role.value}-{packet.period}-{idx:02d}-{kind.value}",packet.role,kind,params,target))
    return actions


def _clamp01(x: float) -> float:
    return max(0.0,min(1.0,x))


def _m_state_from_packet(packet: Packet) -> tuple[float,float,float,float,float]:
    pp=packet.direct_observations.get("own_pp",{})
    inv=packet.direct_observations.get("inventory",{})
    return (
        float(packet.direct_observations.get("cash_k",0)),
        float(inv.get("s1_boards",0)),
        float(inv.get("kits",0)),
        float(pp.get("assembly",0)),
        float(pp.get("test",0)),
    )


def project_m_action(packet: Packet, action: Action, counter: BudgetCounter, estimator: ScalarEstimator | None=None) -> ProjectedOutcome:
    """Four-transition transparent calibration projector for M.

    It uses only PRE-visible observations/evidence plus public frozen transition rules.
    The purpose is compute calibration and conformance, not primary-result generation.
    """
    cash,boards,kits,assembly,test=_m_state_from_packet(packet)
    customer_reserve=float(packet.direct_observations.get("customer_reserve",120))
    s1_line=90.0; s1_quality=90.0
    if estimator is not None:
        if "S1.line" in estimator.beliefs: s1_line=estimator.beliefs["S1.line"].value
        if "S1.quality" in estimator.beliefs: s1_quality=estimator.beliefs["S1.quality"].value
    else:
        for e in packet.evidence:
            if e.claim_family=="supplier_status" and e.payload.get("mode")=="exact":
                s1_line=float(e.payload.get("line",s1_line)); s1_quality=float(e.payload.get("quality",s1_quality))

    adaptation=0.0; irreversible=0.0; quality_loss=0.0; capability_loss=0.0
    commitment_loss=0.0; shortage=0.0; cash_loss=0.0; recovery_loss=0.0
    critical_damage=False; valid=True

    for step in range(counter.budget.horizon):
        counter.consume()
        supply=min(90.0,s1_line)
        boards += supply
        produced=min(80.0,boards,kits,assembly,test)

        if step==0:
            if action.kind is ActionKind.ROUTINE_PRODUCE:
                produced=min(float(action.params.get("units",80)),boards,kits,assembly,test)
            elif action.kind is ActionKind.S1_ASSIST:
                cash-=40; adaptation+=.40; s1_line=min(100,s1_line+15); s1_quality=min(100,s1_quality+20); recovery_loss-=.25
            elif action.kind is ActionKind.START_S2_QUAL:
                cash-=35; adaptation+=.35; capability_loss+=.20
            elif action.kind is ActionKind.RESERVE_S2:
                cash-=20; adaptation+=.20; recovery_loss-=.15
            elif action.kind is ActionKind.SHORTCUT_REWORK:
                cash-=25; adaptation+=.25; test=max(0,test-10); quality_loss+=.25
            elif action.kind is ActionKind.FULL_REWORK:
                cash-=35; adaptation+=.35; test=max(0,test-15); quality_loss+=.08
            elif action.kind is ActionKind.ENHANCED_INSPECT:
                test=max(0,test-10); adaptation+=.10; quality_loss=max(0,quality_loss-.08)
            elif action.kind is ActionKind.FULL_CONTAINMENT:
                test=max(0,test-20); adaptation+=.20; quality_loss=max(0,quality_loss-.15)
            elif action.kind is ActionKind.REQUEST_FINANCE:
                adaptation+=.08; recovery_loss-=.05
            elif action.kind is ActionKind.REQUEST_RENEGOTIATION:
                adaptation+=.05; commitment_loss=max(0,commitment_loss-.10)
            elif action.kind is ActionKind.ORDER_S1:
                # Standing S1 supply is already represented in this neutral calibration projector;
                # the one-period order therefore carries no invented incremental benefit/cost.
                pass
            elif action.kind is ActionKind.ORDER_S2:
                if not bool(packet.direct_observations.get("s2_qualified",False)):
                    valid=False
            elif action.kind is ActionKind.CANCEL:
                if not action.params.get("commitment_id"):
                    valid=False

        boards=max(0,boards-produced); kits=max(0,kits-produced)
        delivered=produced
        if delivered<80:
            shortage += (80-delivered)/80
            commitment_loss += (80-delivered)/80
            customer_reserve=max(0,customer_reserve-(80-delivered))
        else:
            customer_reserve=min(120,customer_reserve+(delivered-80)*.25)

        if s1_quality<70:
            quality_loss += (70-s1_quality)/70*.20
        if s1_line<70:
            recovery_loss += (70-s1_line)/70*.20
        if cash<0:
            cash_loss += min(2.0,abs(cash)/100)
        if customer_reserve<=0:
            irreversible += 2.0; critical_damage=True
        s1_line=max(0,s1_line-3 if s1_line<85 else s1_line)
        s1_quality=max(0,s1_quality-4 if s1_quality<85 else s1_quality)

    losses={
        "commitment":max(0,commitment_loss), "shortage":max(0,shortage),
        "cash":max(0,cash_loss), "capability":max(0,capability_loss),
        "quality":max(0,quality_loss), "adaptation":max(0,adaptation),
        "recovery":max(0,recovery_loss+irreversible),
    }
    governing=(losses["commitment"],losses["shortage"],losses["recovery"])
    all_domain=tuple(losses[k] for k in ("commitment","shortage","cash","capability","quality","adaptation","recovery"))
    adequate=(customer_reserve>0 and cash>=0 and not critical_damage)
    return ProjectedOutcome(action,losses,governing,all_domain,valid,adequate,critical_damage)


class PVPPControllerA:
    def __init__(self, budget: ProjectionBudget | None=None):
        self.budget=budget or ProjectionBudget()
        self.sigma=SigmaSelector()

    def decide(self, packet: Packet) -> DecisionTrace:
        if packet.kind is not PacketKind.PRE: raise ValueError("A accepts PRE only")
        counter=BudgetCounter(self.budget)
        actions=default_action_candidates(packet)
        outcomes=[]; exhausted=False
        for a in actions:
            try:
                outcomes.append(project_m_action(packet,a,counter,None) if packet.role is Role.M else ProjectedOutcome(a,{},(0,),(0,),True,True,False))
            except PlanningBudgetExceeded:
                exhausted=True; break
        if not outcomes:
            no=next(a for a in actions if a.kind is ActionKind.NO_ACTION)
            return DecisionTrace("A",packet.role,packet.period,no,len(actions),0,counter.evaluations,counter.elapsed,True,("SEARCH_BUDGET_EXHAUSTED",))
        cands=[Candidate(o.action.action_id,o.valid,o.adequate,o.governing,o.all_domain,o.irreversible_critical_damage) for o in outcomes]
        selected=self.sigma.select(cands)
        if selected is None:
            chosen=next((o.action for o in outcomes if o.action.kind is ActionKind.NO_ACTION),outcomes[0].action)
        else:
            chosen=next(o.action for o in outcomes if o.action.action_id==selected.policy_id)
        notes=("SEARCH_BUDGET_EXHAUSTED",) if exhausted else ()
        return DecisionTrace("A",packet.role,packet.period,chosen,len(actions),len(outcomes),counter.evaluations,counter.elapsed,exhausted,notes)


class ScalarControllerB:
    def __init__(self, budget: ProjectionBudget | None=None, panel: str="B0"):
        self.budget=budget or ProjectionBudget(); self.panel=panel; self.estimator=ScalarEstimator()

    def _weights(self, role: Role) -> dict[str,float]:
        w=dict(BASE_B_WEIGHTS[role])
        if role is not Role.M or self.panel=="B0": return w
        if self.panel=="B1":
            for k in ("commitment","shortage"): w[k]*=1.25
            w["adaptation"]*=.8; w["cash"]*=.9
        elif self.panel=="B2":
            for k in ("capability","quality","recovery"): w[k]*=1.25
            w["adaptation"]*=.8; w["commitment"]*=.9
        elif self.panel=="B3":
            w["cash"]*=1.35; w["adaptation"]*=1.15; w["commitment"]*=.9
        elif self.panel=="B4":
            w["quality"]*=1.5; w["commitment"]*=.85; w["adaptation"]*=.9
        return w

    @staticmethod
    def _score(losses: dict[str,float], weights: dict[str,float]) -> float:
        # Calibration implementation uses deterministic horizon loss. Stochastic CVaR
        # is exercised in the later event-path calibration, before execution unlock.
        return sum(weights.get(k,0.0)*v for k,v in losses.items())

    def decide(self, packet: Packet) -> DecisionTrace:
        if packet.kind is not PacketKind.PRE: raise ValueError("B accepts PRE only")
        self.estimator.absorb(packet)
        counter=BudgetCounter(self.budget); actions=default_action_candidates(packet)
        outcomes=[]; exhausted=False
        for a in actions:
            try:
                outcomes.append(project_m_action(packet,a,counter,self.estimator) if packet.role is Role.M else ProjectedOutcome(a,{},(0,),(0,),True,True,False))
            except PlanningBudgetExceeded:
                exhausted=True; break
        if not outcomes:
            chosen=next(a for a in actions if a.kind is ActionKind.NO_ACTION)
        else:
            weights=self._weights(packet.role)
            chosen=min(outcomes,key=lambda o:(self._score(o.losses,weights),o.action.action_id)).action
        self.estimator.propagate_freshness(1)
        notes=("SEARCH_BUDGET_EXHAUSTED",) if exhausted else ()
        return DecisionTrace(f"B-{self.panel}",packet.role,packet.period,chosen,len(actions),len(outcomes),counter.evaluations,counter.elapsed,exhausted,notes)
