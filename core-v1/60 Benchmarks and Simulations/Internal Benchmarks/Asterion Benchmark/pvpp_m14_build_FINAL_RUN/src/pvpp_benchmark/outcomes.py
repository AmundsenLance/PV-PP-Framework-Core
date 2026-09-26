from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, Any
from .model import Role

@dataclass(frozen=True)
class OutcomeSummary:
    committed_units: float
    delivered_units: float
    raw_delivery_shortfall: float
    unrenegotiated_shortfall: float
    breach_strikes_total: int
    renegotiated_reduction: float
    physical_shortage_unit_weeks: float
    customer_reserve_min: float
    customer_reserve_terminal: float
    inspection_events: int
    qualification_stage_failures: int
    delayed_field_failures: int
    major_field_events: int
    customer_terminated: bool
    customer_business_collapse: bool
    customer_collapse_right_censored: bool
    customer_operations_pp_terminal: float
    supplier_exits: int
    credit_draw_k: float
    adaptation_cost_k: float
    transport_delay_events: int
    irreversible_events: int
    ledger_entries: int
    decision_evaluations: int
    decision_transition_evaluations: int
    decision_timeouts: int
    m_cash_min: float
    m_cash_terminal: float
    covenant_headroom_min: float
    covenant_headroom_terminal: float
    pp_preservation: dict[str, dict[str, float | int]]
    restoration_actions: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def reconstruct_outcomes(world, decision_traces: Iterable[Any]=(), state_history: Iterable[dict[str,Any]]=()) -> OutcomeSummary:
    """Reconstruct predeclared V2 outcome families from the immutable ledger.

    This extractor intentionally does not produce a cross-domain/global score. It derives
    auditable metric components only. PP-domain trajectory reconstruction is handled by the
    runner snapshot extension because PP values are state variables rather than ledger events.
    """
    entries=world.ledger.entries
    period_end=[e for e in entries if e.family=='customer_period_end']
    delivered=sum(float(e.payload.get('delivered',0)) for e in period_end)
    committed=sum(float(e.payload.get('commitment',80)) for e in period_end)
    raw_short=sum(max(0.0,float(e.payload.get('commitment',80))-float(e.payload.get('delivered',0))) for e in period_end)
    reneg=sum(float(e.payload.get('reduction',0)) for e in entries if e.family=='renegotiation_accepted')
    # Frozen distinction: physical demand remains 80 even after contract concession.
    physical_short=sum(max(0.0,80.0-float(e.payload.get('delivered',0))) for e in period_end)
    reserves=[float(e.payload.get('reserve',0)) for e in period_end]
    qual_fail=sum(1 for e in entries if e.family=='s2_qualification_stage' and not bool(e.payload.get('passed',False)))
    field=sum(1 for e in entries if e.family=='major_field_quality_event')
    delayed_field=sum(int(e.payload.get('failures',0)) for e in entries if e.family=='major_field_quality_event')
    draws=sum(float(e.payload.get('amount_k',0)) for e in entries if e.family=='credit_draw')
    cost_families={
        's2_qualification_started':'cash_cost_k','s2_capacity_reserved':'cash_cost_k',
        's1_assistance':'cash_cost_k','rework_batch':'cash_cost_k','full_rework_started':'cash_cost_k',
    }
    adaptation=0.0
    for e in entries:
        if e.family in cost_families:
            adaptation += float(e.payload.get(cost_families[e.family],0) or 0)
    irreversible=sum(1 for e in entries if e.family in {'customer_termination','supplier_exit','line_shutdown','financing_closure'})
    # customer_period_end records the full rolling strike count, not newly-created strikes.
    # Count actual strike creation from missing quantities according to frozen rule.
    strike_total=sum(2 if float(e.payload.get('missing',0))>50 else (1 if float(e.payload.get('missing',0))>20 else 0) for e in period_end)
    traces=list(decision_traces)
    hist=list(state_history)
    if not hist:
        s=world.state
        hist=[{"m_cash_k":float(s.agents[Role.M].cash_k),"headroom":float(getattr(s,"m_covenant_headroom",1.0)),
               "pp":{r.value:dict(a.pp) for r,a in s.agents.items()}}]
    cash_vals=[float(x.get("m_cash_k",0)) for x in hist]
    head_vals=[float(x.get("headroom",1.0)) for x in hist]
    pp_series={}
    for snap in hist:
        for role,domains in snap.get("pp",{}).items():
            for domain,val in domains.items(): pp_series.setdefault(f"{role}.{domain}",[]).append(float(val))
    pp_pres={}
    for key,vals in pp_series.items():
        # Critical-band convention for reporting is 70 PP; this does not alter controller feasibility.
        pp_pres[key]={"initial":vals[0],"minimum":min(vals),"terminal":vals[-1],"periods_below_70":sum(v<70 for v in vals)}
    restoration=sum(1 for e in entries if e.family in {'s1_recovery','s1_assistance','full_rework_completed'})
    return OutcomeSummary(
        committed_units=committed, delivered_units=delivered, raw_delivery_shortfall=raw_short,
        unrenegotiated_shortfall=max(0.0,raw_short-reneg), breach_strikes_total=strike_total,
        renegotiated_reduction=reneg, physical_shortage_unit_weeks=physical_short,
        customer_reserve_min=min(reserves) if reserves else float(world.state.customer_reserve),
        customer_reserve_terminal=float(world.state.customer_reserve), inspection_events=sum(1 for e in entries if e.family=='inspection'),
        qualification_stage_failures=qual_fail, delayed_field_failures=delayed_field, major_field_events=field,
        customer_terminated=bool(world.state.customer_terminated),
        customer_business_collapse=float(world.state.agents[Role.C].pp.get("operations",0.0))<=0.0,
        customer_collapse_right_censored=(float(world.state.agents[Role.C].pp.get("operations",0.0))<=0.0 and not bool(world.state.customer_terminated)),
        customer_operations_pp_terminal=float(world.state.agents[Role.C].pp.get("operations",0.0)),
        supplier_exits=sum(1 for e in entries if e.family=='supplier_exit'),
        credit_draw_k=draws, adaptation_cost_k=adaptation, transport_delay_events=sum(1 for e in entries if e.family=='transport_delay'),
        irreversible_events=irreversible, ledger_entries=len(entries),
        decision_evaluations=sum(int(getattr(t,'evaluated_count',0)) for t in traces),
        decision_transition_evaluations=sum(int(getattr(t,'transition_evaluations',0)) for t in traces),
        decision_timeouts=sum(1 for t in traces if bool(getattr(t,'budget_exhausted',False))),
        m_cash_min=min(cash_vals), m_cash_terminal=cash_vals[-1],
        covenant_headroom_min=min(head_vals), covenant_headroom_terminal=head_vals[-1],
        pp_preservation=pp_pres, restoration_actions=restoration,
    )
