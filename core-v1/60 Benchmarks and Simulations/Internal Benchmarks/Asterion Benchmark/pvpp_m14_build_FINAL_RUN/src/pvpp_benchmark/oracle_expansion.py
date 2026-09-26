from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from math import floor
from typing import Callable, Iterable

from .model import Action, ActionKind, Role, WorldState
from .world import AsterionWorld
from .engine import AsterionTransitionEngine
from .oracle_search import OracleClassification, OracleSearchResult, simple_recovery_predicate

@dataclass(frozen=True)
class JointActionPlan:
    plan_id: str
    actions: tuple[Action,...]

@dataclass(frozen=True)
class GrammarCompleteness:
    complete: bool
    incomplete_families: tuple[str,...] = ()
    note: str = ""


def _a(pid: str, kind: ActionKind, params=None, target=None) -> Action:
    return Action(pid,Role.M,kind,params or {},target)


def integer_lattice_max_production(state: WorldState) -> int:
    """Exact integer quantity ceiling induced by current frozen resources.

    v0.2 states physical units are integer units; v0.4 bounds realized production by
    accessible boards, kits, assembly/test slots and cash.  No coarse quantity grid is used.
    """
    m=state.agents[Role.M]
    boards=floor(m.inventory.get("s1_boards",0)+m.inventory.get("s2_boards",0))
    kits=floor(m.inventory.get("kits",0))
    assembly=floor(max(0,m.pp.get("assembly",0)-m.encumbered.get("assembly",0)))
    test=floor(max(0,m.pp.get("test",0)-m.encumbered.get("test",0)))
    cash=floor(max(0,m.cash_k)/3)
    return max(0,min(boards,kits,assembly,test,cash))


def licensed_integer_flow_plans(state: WorldState) -> Iterable[JointActionPlan]:
    """Lazy exact integer lattice for currently executable M flow actions.

    Every integer production quantity is considered.  For each such quantity, every integer
    shipment quantity reachable from beginning inventory plus that production is considered.
    This is intentionally large; the oracle budget may therefore terminate as UNDETERMINED.
    """
    p=state.period
    m=state.agents[Role.M]
    max_prod=integer_lattice_max_production(state)
    starting_finished=floor(m.inventory.get("finished",0))
    # A no-action plan is a licensed root policy.
    yield JointActionPlan("flow-p0-s0",(_a(f"O-{p}-noop",ActionKind.NO_ACTION),))
    for prod in range(0,max_prod+1):
        max_ship=starting_finished+prod
        for ship in range(0,max_ship+1):
            if prod==0 and ship==0:
                continue
            acts=[]
            if prod:
                acts.append(_a(f"O-{p}-prod-{prod}",ActionKind.ROUTINE_PRODUCE,{"units":prod}))
            if ship:
                acts.append(_a(f"O-{p}-ship-{ship}",ActionKind.SHIP,{"units":ship},Role.C))
            yield JointActionPlan(f"flow-p{prod}-s{ship}",tuple(acts))


def grammar_completeness(state: WorldState) -> GrammarCompleteness:
    """v0.12 contract/transformation completeness certificate.

    Counterpart_Contract_v012 narrows the previously open contract families to explicit finite
    benchmark fixtures.  Computational exhaustion may still fail on budget, but there is no
    longer an undeclared parameter interpolation in the modeled primary action surface.
    """
    return GrammarCompleteness(True,(),
        "v0.12 closes the five counterpart/contract semantic gaps; exhaustive proof still requires actual tree exhaustion within the frozen budget.")


def frozen_oracle_root_plans(state: WorldState) -> tuple[JointActionPlan,...]:
    """Pre-lock diagnostic expansion without an invented quantity grid.

    It contains the exact integer lattice for the currently complete M flow semantics and a small
    set of other parameterizations whose numerical transformation is explicitly frozen.  Because
    the complete multi-agent catalog is not yet semantically executable, this function is *not*
    a completeness certificate and cannot support PROVEN_INFEASIBLE by exhaustion.
    """
    p=state.period
    plans=list(licensed_integer_flow_plans(state))
    singles=(
        ("assist",ActionKind.S1_ASSIST,{},Role.S1),
        ("qual-normal",ActionKind.START_S2_QUAL,{"emergency":False},Role.S2),
        ("qual-emergency",ActionKind.START_S2_QUAL,{"emergency":True},Role.S2),
        # Only the explicitly costed reservation point is executable without interpolation.
        ("reserve-s2-60",ActionKind.RESERVE_S2,{"capacity":60},Role.S2),
        # v0.12 current-period customer renegotiation lattice.
        ("inspect",ActionKind.INSPECT,{},None),
        ("enhanced",ActionKind.ENHANCED_INSPECT,{},None),
        ("contain",ActionKind.FULL_CONTAINMENT,{},None),
        ("shortcut-20",ActionKind.SHORTCUT_REWORK,{"units":20},None),
        ("shortcut-40",ActionKind.SHORTCUT_REWORK,{"units":40},None),
        ("full-rework-20",ActionKind.FULL_REWORK,{"units":20},None),
        ("full-rework-40",ActionKind.FULL_REWORK,{"units":40},None),
    )
    # v0.12 customer renegotiation uses every licensed integer q in [60,80].
    for q in range(60,81):
        singles += ((f"reneg-c-{q}",ActionKind.REQUEST_RENEGOTIATION,{"delivery":q},Role.C),)
    # v0.12 one-period supplier order lattices.
    for q in range(0,91):
        singles += ((f"order-s1-{q}",ActionKind.ORDER_S1,{"quantity":q},Role.S1),)
    if state.s2_qualified:
        cap=int(max(0,state.agents[Role.S2].pp.get("line",0)-state.s2_external_encumbrance))
        if state.s2_emergency_conditional: cap=min(40,cap)
        for q in range(0,cap+1):
            singles += ((f"order-s2-{q}",ActionKind.ORDER_S2,{"quantity":q},Role.S2),)
    # Future-only cancellable commitments are finite and named.
    for cid,c in sorted(state.commitments.items()):
        if c.active and c.start_period>state.period and c.family in ("s2_capacity","s1_order","s2_order","s2_qualification"):
            singles += ((f"cancel-{cid}",ActionKind.CANCEL,{"commitment_id":cid},None),)

    # Credit draw has an explicit $50k lattice up to current facility availability.
    avail=int(max(0,getattr(state,"m_credit_available_k",500))//50)*50
    for amount in range(50,avail+1,50):
        singles += ((f"finance-{amount}",ActionKind.REQUEST_FINANCE,{"amount_k":amount},Role.L),)
    for name,k,params,target in singles:
        plans.append(JointActionPlan(name,(_a(f"O-{p}-{name}",k,params,target),)))
    w=world_from_state(state); e=AsterionTransitionEngine(w)
    out=[]
    for plan in plans:
        res=e.resolve_joint(plan.actions)
        if len(res.accepted)==len(plan.actions):
            out.append(plan)
    return tuple(out)


def world_from_state(state: WorldState, seed: int=0) -> AsterionWorld:
    w=AsterionWorld(seed); w.state=deepcopy(state); return w


def oracle_step_plan(state: WorldState, plan: JointActionPlan) -> WorldState:
    w=world_from_state(state); e=AsterionTransitionEngine(w); e.realize(plan.actions,advance=True); return deepcopy(w.state)


class ExactFiniteOracleSearcher:
    """Finite diagnostic search with conservative proof classification.

    Exhaustion yields PROVEN_INFEASIBLE only when the supplied grammar carries a validated
    completeness certificate.  The default pre-lock grammar is deliberately incomplete, so
    exhaustion is UNDETERMINED rather than a false world-infeasibility claim.
    """
    def search(self, initial: WorldState, horizon: int, budget: int,
               expander: Callable[[WorldState],Iterable[JointActionPlan]]=frozen_oracle_root_plans,
               recovery: Callable[[WorldState],bool]=simple_recovery_predicate,
               completeness: Callable[[WorldState],GrammarCompleteness]=grammar_completeness) -> OracleSearchResult:
        from collections import deque
        if recovery(initial): return OracleSearchResult(OracleClassification.RECOVERY_FOUND,0,0,(),True)
        q=deque([(deepcopy(initial),0,())]); explored=0
        while q:
            state,depth,path=q.popleft()
            if depth>=horizon: continue
            for plan in expander(state):
                if explored>=budget:
                    return OracleSearchResult(OracleClassification.UNDETERMINED,explored,depth,path,False)
                explored+=1
                nxt=oracle_step_plan(state,plan); np=path+(plan.plan_id,)
                if recovery(nxt): return OracleSearchResult(OracleClassification.RECOVERY_FOUND,explored,depth+1,np,False)
                q.append((nxt,depth+1,np))
        cert=completeness(initial)
        if cert.complete:
            return OracleSearchResult(OracleClassification.PROVEN_INFEASIBLE,explored,horizon,(),True)
        return OracleSearchResult(OracleClassification.UNDETERMINED,explored,horizon,(),False)

@dataclass(frozen=True)
class OracleProtocolResult:
    o1: OracleSearchResult
    o2: OracleSearchResult | None

class O1O2OracleProtocol:
    def __init__(self, searcher: ExactFiniteOracleSearcher | None=None):
        self.searcher=searcher or ExactFiniteOracleSearcher()

    def run_o1(self, state: WorldState, expander=frozen_oracle_root_plans,
               recovery=simple_recovery_predicate, completeness=grammar_completeness) -> OracleSearchResult:
        return self.searcher.search(state,horizon=8,budget=250_000,expander=expander,recovery=recovery,completeness=completeness)

    def run_o2(self, state: WorldState, remaining_trace_horizon: int,
               expander=frozen_oracle_root_plans, recovery=simple_recovery_predicate,
               completeness=grammar_completeness) -> OracleSearchResult:
        horizon=max(1,min(12,int(remaining_trace_horizon)))
        return self.searcher.search(state,horizon=horizon,budget=1_000_000,expander=expander,recovery=recovery,completeness=completeness)

    def classify(self, state: WorldState, remaining_trace_horizon: int,
                 expander=frozen_oracle_root_plans, recovery=simple_recovery_predicate,
                 completeness=grammar_completeness) -> OracleProtocolResult:
        o1=self.run_o1(state,expander,recovery,completeness)
        if o1.classification is OracleClassification.RECOVERY_FOUND:
            return OracleProtocolResult(o1,None)
        o2=self.run_o2(state,remaining_trace_horizon,expander,recovery,completeness)
        return OracleProtocolResult(o1,o2)
