from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from typing import Iterable

from .model import Action, ActionKind, Evidence, EvidenceStatus, Role
from .world import AsterionWorld
from .engine import AsterionTransitionEngine

@dataclass(frozen=True)
class ScenarioSnapshot:
    period: int
    customer_reserve: float
    m_cash_k: float
    s1_line: float
    s1_quality: float
    s2_qualified: bool
    s2_external_encumbrance: float
    r_emergency_active: bool
    customer_terminated: bool

@dataclass
class MultiAgentScenarioRunner:
    """Calibration-only multi-agent Asterion scenario runner.

    It advances the frozen public world clock and counterpart/exogenous mechanics without
    invoking A/B/C comparative outcome generation. Caller supplies M's current-period
    root actions. Counterpart/exogenous behavior is common and regime-blind.
    """
    world: AsterionWorld
    deterministic: bool = True
    history: list[ScenarioSnapshot] = field(default_factory=list)

    def __post_init__(self):
        self.engine=AsterionTransitionEngine(self.world)
        s=self.world.state
        s.__dict__.setdefault("s1_onset_period", 3)
        s.__dict__.setdefault("s1_deterioration_active", False)
        s.__dict__.setdefault("s2_opportunity_announced", False)
        s.__dict__.setdefault("s2_opportunity_closed", False)
        s.__dict__.setdefault("s1_last_supply", 0.0)
        s.__dict__.setdefault("s2_last_supply", 0.0)

    def _apply_period_start_exogenous(self):
        s=self.world.state; p=s.period
        # Deterministic challenge uses P3 and 15/20. Stochastic primary runs supply the
        # frozen onset/severity fixture through semantic seed-keyed state fields.
        onset = 3 if self.deterministic else int(getattr(s,"stochastic_primary_onset",3))
        initial = (15,20) if self.deterministic else tuple(getattr(s,"stochastic_initial_dec",(15,20)))
        if p==onset and not s.s1_deterioration_active:
            self.world.deteriorate_s1(p,*initial); s.s1_deterioration_active=True
        elif p>onset and s.s1_deterioration_active:
            if self.deterministic:
                dec=(8,10)
            else:
                sev=self.world.rng.choice([(5,7),(8,10),(11,13)],[.25,.5,.25],"s1_untreated",p)
                dec=sev
            self.world.deteriorate_s1(p,*dec)
        if s.s1_deterioration_active:
            self.world.s1_message(p)
        if p==6 and not s.s2_opportunity_announced:
            self.world.activate_s2_external_opportunity(); s.s2_opportunity_announced=True
        if p==7 and not s.s2_opportunity_closed:
            self.world.close_s2_opportunity_if_unreserved(s.s2_reserved_capacity>0)
            s.s2_opportunity_closed=True
        # Frozen deterministic transport stress state changes.
        if p==5: s.transport_state="MEDIUM"
        if p==9: s.transport_state="HIGH"
        if p==12: s.transport_state="MEDIUM"

    def _common_counterpart_supply(self):
        s=self.world.state; m=s.agents[Role.M]; s1=s.agents[Role.S1]; s2=s.agents[Role.S2]
        # S1 physical supply is bounded by line PP and the live current-period commitment.
        live_s1=[c for c in s.commitments.values() if c.active and c.family=="s1_order" and c.start_period==s.period]
        ordered_s1=float(live_s1[-1].quantity) if live_s1 else 90.0
        s1_supply=max(0.0,min(ordered_s1,float(s1.pp.get("line",0.0))))
        purchase1=2.0*s1_supply
        if m.cash_k>=purchase1:
            m.cash_k-=purchase1; s1.cash_k+=purchase1
            m.inventory["s1_boards"]=m.inventory.get("s1_boards",0.0)+s1_supply
        else:
            s1_supply=0.0
        s.s1_last_supply=s1_supply
        self.world.ledger.append(s.period,"s1_supply_arrival",units=s1_supply,cash_paid_k=2.0*s1_supply)
        # Mechanical kits replenish at 95/week in the frozen world.
        m.inventory["kits"]=m.inventory.get("kits",0.0)+95.0
        self.world.ledger.append(s.period,"kit_supply_arrival",units=95.0)
        # S2 supply requires a live one-period order after qualification. Reservation protects capacity but is not itself an order.
        s2_supply=0.0
        live_s2=[c for c in s.commitments.values() if c.active and c.family=="s2_order" and c.start_period==s.period]
        if s.s2_qualified and live_s2:
            ordered=float(live_s2[-1].quantity)
            physical=max(0.0,float(s2.pp.get("line",0.0))-float(s.s2_external_encumbrance))
            if s.s2_emergency_conditional:
                physical=min(40.0,physical)
            if s.s2_reserved_capacity>0:
                physical=min(physical,s.s2_reserved_capacity)
            s2_supply=min(ordered,physical)
            purchase2=2.6*s2_supply
            if m.cash_k>=purchase2:
                m.cash_k-=purchase2; s2.cash_k+=purchase2
                m.inventory["s2_boards"]=m.inventory.get("s2_boards",0.0)+s2_supply
            else:
                s2_supply=0.0
            self.world.ledger.append(s.period,"s2_supply_arrival",units=s2_supply,cash_paid_k=2.6*s2_supply)
        s.s2_last_supply=s2_supply

    def _common_institutional_checks(self):
        s=self.world.state
        if not s.r_emergency_active and s.s1_deterioration_active:
            # R uses world evidence/rules, not controller recovery projections.
            line=float(s.agents[Role.S1].pp.get("line",0.0))
            certified=(line,line)
            self.world.r_emergency_check(certified,80.0,False)

    def step(self, m_actions: Iterable[Action]=()):
        self._apply_period_start_exogenous()
        self._common_counterpart_supply()
        self._common_institutional_checks()
        result=self.engine.realize(tuple(m_actions),advance=True)
        s=self.world.state
        snap=ScenarioSnapshot(s.period,s.customer_reserve,s.agents[Role.M].cash_k,
                              s.agents[Role.S1].pp.get("line",0),s.agents[Role.S1].pp.get("quality",0),
                              s.s2_qualified,s.s2_external_encumbrance,s.r_emergency_active,s.customer_terminated)
        self.history.append(snap)
        return result

    def run_script(self, script: dict[int, tuple[Action,...]], through_period: int):
        while self.world.state.period<=through_period and not self.world.state.customer_terminated:
            self.step(script.get(self.world.state.period,()))
        return tuple(self.history)
