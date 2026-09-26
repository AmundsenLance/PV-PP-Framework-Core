from __future__ import annotations
import json, hashlib
from pathlib import Path
from pvpp_benchmark.world import AsterionWorld
from pvpp_benchmark.scenario import MultiAgentScenarioRunner
from pvpp_benchmark.model import Action, ActionKind, Role
from pvpp_benchmark.production import ProductionRolePolicy, _m_root_actions
from pvpp_benchmark.oracle_expansion import frozen_oracle_root_plans, O1O2OracleProtocol, GrammarCompleteness, grammar_completeness

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'config'/'prelock_validation.json'

w=AsterionWorld(777)
r=MultiAgentScenarioRunner(w)
rows=[]
for _ in range(17):
    p=w.state.period
    acts=(Action(f'P{p}-prod',Role.M,ActionKind.ROUTINE_PRODUCE,{'units':80}),
          Action(f'P{p}-ship',Role.M,ActionKind.SHIP,{'units':80},Role.C))
    tr=r.step(acts)
    s=w.state
    rows.append({
        'decision_period':p,'next_period':s.period,
        'rejected':[{'action':a.action_id,'reason':reason} for a,reason in tr.rejected_actions],
        'm_cash_k':s.agents[Role.M].cash_k,
        's1_line':s.agents[Role.S1].pp['line'],'s1_quality':s.agents[Role.S1].pp['quality'],
        'customer_reserve':s.customer_reserve,'customer_terminated':s.customer_terminated,
        'r_emergency_active':s.r_emergency_active,'s2_external_encumbrance':s.s2_external_encumbrance,
        'ledger_entries':len(w.ledger.entries),
    })
    if s.customer_terminated: break

initial=AsterionWorld(778).state
plans=frozen_oracle_root_plans(initial)
plan_families=sorted({a.kind.value for p in plans for a in p.actions})
protocol=O1O2OracleProtocol()
# Microfixtures validate exhaustive labels without launching a giant tree.
terminal=AsterionWorld(779).state; terminal.customer_terminated=True; terminal.customer_reserve=0
empty=lambda s: ()
pr=protocol.classify(terminal,remaining_trace_horizon=20,expander=empty, completeness=lambda s: GrammarCompleteness(True,(),"microfixture complete"))
default_cert=grammar_completeness(initial)

# Controller-aware termination microfixture.  The generic physical trace intentionally has no C
# controller, so terminalization is not expected there after the v0.4 correction.
cw=AsterionWorld(780); cw.state.customer_reserve=20; cw.state.customer_termination_eligible=True
ct=ProductionRolePolicy('A',Role.C).decide(cw.packet(Role.C),780).action
customer_termination_choice_verified=(ct.kind is ActionKind.C_TERMINATE)

# M action-surface state fixtures prove state-gated families become reachable without forcing them
# into calm states where they are ineligible.
mw=AsterionWorld(781); calm_kinds={a.kind.value for a in _m_root_actions(mw.packet(Role.M))}
mw.state.m_covenant_headroom=.20; mw.state.agents[Role.M].pp['assembly']=80
stress_kinds={a.kind.value for a in _m_root_actions(mw.packet(Role.M))}
required_m_families={x.value for x in (ActionKind.M_CONSERVE,ActionKind.M_RATION,ActionKind.M_SPLIT_SOURCE,ActionKind.M_BOOK_T,ActionKind.M_AMEND_L,ActionKind.M_RECOVER_PP,ActionKind.M_PAUSE,ActionKind.M_BREACH_CONTROLLED,ActionKind.M_SHUT_LINE)}

payload={
  'mode':'CALIBRATION_CONFORMANCE_ONLY',
  'primary_comparative_execution':False,
  'scenario_seed':777,
  'scenario_period_rows':rows,
  'scenario_terminal_period':w.state.period if w.state.customer_terminated else None,
  'milestones':{
      's1_deterioration_seen':any(x['decision_period']>=3 and x['s1_line']<100 for x in rows),
      'r_emergency_seen':any(x['r_emergency_active'] for x in rows),
      's2_external_encumbrance_seen':any(x['s2_external_encumbrance']>0 for x in rows),
      'controller_free_trace_does_not_auto_terminate':not any(x['customer_terminated'] for x in rows),
      'customer_termination_choice_verified':customer_termination_choice_verified,
      'required_m_action_families_reachable':required_m_families <= stress_kinds,
  },
  'oracle_expansion':{
      'initial_feasible_plan_count':len(plans),
      'action_families':plan_families,
      'contains_joint_production_shipment':any(len(p.actions)==2 for p in plans),
      'default_grammar_complete':default_cert.complete,
      'default_incomplete_family_count':len(default_cert.incomplete_families),
      'o1_horizon':8,'o1_budget':250000,'o2_horizon_cap':12,'o2_budget':1000000,
      'empty_tree_o1_classification':pr.o1.classification.value,
      'empty_tree_o2_classification':pr.o2.classification.value if pr.o2 else None,
  }
}
OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
print(OUT)
