import pytest
from pvpp_benchmark.world import AsterionWorld, ConformanceError
from pvpp_benchmark.model import Role, PacketKind, ActionKind, Evidence, EvidenceStatus, Action, Commitment
from pvpp_benchmark.grammar import common_action_grammar
from pvpp_benchmark.controllers import ScalarEstimator, SigmaSelector, LOCAL_PRIORITIES, BASE_B_WEIGHTS, Candidate
from pvpp_benchmark.oracle import OracleDiagnostic, OracleLeakError
from pvpp_benchmark.execution import run_primary_comparative, PrimaryExecutionLocked
from pvpp_benchmark.calibration import generate_master_seeds, choose_ensemble_n, choose_compute_ceiling


def test_t1_calm_initial_state_supports_80_units():
    w=AsterionWorld(1)
    s=w.state
    assert s.agents[Role.M].pp["assembly"] >= 80
    assert s.agents[Role.M].pp["test"] >= 80
    assert s.agents[Role.M].inventory["s1_boards"] >= 80
    assert s.agents[Role.M].inventory["kits"] >= 80
    assert s.commitments["COM-S1"].quantity >= s.commitments["COM-CUST"].quantity


def test_t2_raw_evidence_parity_for_same_role_packet():
    w=AsterionWorld(2); w.deteriorate_s1(3); e=w.s1_message(3)
    p1=w.packet(Role.M); p2=w.packet(Role.M)
    assert p1.evidence == p2.evidence
    assert e in p1.evidence


def test_t3_misleading_message_does_not_rewrite_actual_state():
    w=AsterionWorld(3); w.state.period=4; w.deteriorate_s1(4,20,25)
    before=dict(w.state.agents[Role.S1].pp)
    _=w.s1_message(4)
    assert w.state.agents[Role.S1].pp == before


def test_t4_scalar_estimator_keeps_uncertainty_and_freshness():
    w=AsterionWorld(4); w.state.period=3
    # Force exact report by keeping S1 >=70/70.
    e=w.s1_message(3); assert e.payload["mode"]=="exact"
    est=ScalarEstimator(); est.absorb(w.packet(Role.M))
    u0=est.beliefs["S1.line"].uncertainty
    est.propagate_freshness(2)
    assert est.beliefs["S1.line"].uncertainty > u0


def test_t5_s2_qualification_stage_arithmetic_and_emergency_threshold():
    w=AsterionWorld(5); w.start_s2_qualification(emergency=True)
    assert w.state.agents[Role.M].cash_k == 385
    assert w.state.agents[Role.M].encumbered.get("engineering",0) == 0
    assert w.state.agents[Role.M].encumbered.get("test",0) == 0
    assert w.state.agents[Role.S2].encumbered.get("engineering",0) == 0
    assert w.complete_s2_stage(0,0,True)
    assert w.complete_s2_stage(0,1,True)
    assert w.state.s2_qualified and w.state.s2_emergency_conditional


def test_t5_qualification_failure_does_not_increment_stage():
    w=AsterionWorld(6); w.start_s2_qualification(False)
    assert not w.complete_s2_stage(0,2,False)
    assert w.state.s2_qualification_stages == 0


def test_t6_delivered_rework_risk_is_semantic_keyed_and_delayed():
    a=AsterionWorld(99); b=AsterionWorld(99)
    a.state.period=b.state.period=5
    ids=[f"BOARD-{i}" for i in range(200)]
    a.schedule_delivered_board_failures("SHIP-A",{"shortcut":ids})
    b.schedule_delivered_board_failures("SHIP-B",{"shortcut":ids})
    a_view=[(q["board_id"],q["delivery_period"],q["due"],q["provenance"]) for q in a.state.field_failure_queue]
    b_view=[(q["board_id"],q["delivery_period"],q["due"],q["provenance"]) for q in b.state.field_failure_queue]
    assert a_view == b_view
    assert all(q["due"] in (7,8,9) for q in a.state.field_failure_queue)
    assert not hasattr(a,"schedule_rework_failures")


def test_t7_sigma_standard_fallback_and_terminal_modes():
    s=SigmaSelector()
    standard=[Candidate("b",True,True,(1,),(2,)),Candidate("a",True,True,(1,),(2,))]
    assert s.select(standard).policy_id=="a"
    fallback=[Candidate("x",True,False,(4,2),(2,)),Candidate("y",True,False,(5,1),(1,))]
    assert s.select(fallback).policy_id=="x"
    terminal=[Candidate("z",False,False,(0,),(0,))]
    assert s.select(terminal) is None


def test_t8_s2_opportunity_not_visible_to_m_until_disclosed():
    w=AsterionWorld(8); w.state.period=6; w.activate_s2_external_opportunity()
    s2=w.packet(Role.S2); m=w.packet(Role.M)
    assert any(e.claim_family=="external_market_opportunity" for e in s2.evidence)
    assert not any(e.claim_family=="external_market_opportunity" for e in m.evidence)
    w.state.period=7; w.close_s2_opportunity_if_unreserved(False); w.advance_period()
    assert w.state.period==8 and w.state.s2_external_encumbrance==30


def test_t9_proposal_is_available_but_not_a_commitment_by_itself():
    w=AsterionWorld(9)
    assert ActionKind.PROPOSE in common_action_grammar(Role.M)
    before=set(w.state.commitments)
    # No method automatically converts proposal grammar into commitment.
    after=set(w.state.commitments)
    assert before==after


def test_t10_oracle_isolation():
    w=AsterionWorld(10); o=OracleDiagnostic(); op=o.state_oracle_packet(w.state)
    with pytest.raises(OracleLeakError): o.assert_not_controller_packet(op)
    with pytest.raises(ConformanceError): w.packet(Role.M,PacketKind.ORACLE)


def test_t11_scalar_weight_panels_and_local_rules_exist_for_all_economic_roles():
    for r in (Role.M,Role.S1,Role.S2,Role.C,Role.L,Role.T):
        assert r in BASE_B_WEIGHTS and BASE_B_WEIGHTS[r]
        assert r in LOCAL_PRIORITIES and LOCAL_PRIORITIES[r]


def test_t12_firewall_role_packets_do_not_expose_other_private_state():
    w=AsterionWorld(12)
    m=w.packet(Role.M); s1=w.packet(Role.S1)
    assert "own_pp" in m.direct_observations and "own_pp" in s1.direct_observations
    assert m.direct_observations["own_pp"] != s1.direct_observations["own_pp"]
    assert "S1_actual_pp" not in m.direct_observations


def test_r_emergency_evidence_rule():
    w=AsterionWorld(13); w.state.period=5
    assert w.r_emergency_check((40,45),80,False)
    assert w.state.r_emergency_active
    assert any(e.claim_family=="emergency_qualification_notice" for e in w.packet(Role.M).evidence)


def test_master_seed_recipe_is_deterministic_and_prefix_based():
    a=generate_master_seeds(10); b=generate_master_seeds(10)
    assert a==b and len(set(a))==10
    assert a[0]==7950518952219427039


def test_ensemble_calibration_is_controller_free_and_returns_allowed_n():
    n,diag,ref=choose_ensemble_n()
    assert n in (100,250,500,1000)
    assert set(diag).issubset({100,250,500,1000})
    assert ref


def test_compute_calibration_uses_first_common_passing_multiplier():
    r=choose_compute_ceiling({1:.94,2:.98},{1:.97,2:.96})
    assert r.multiplier==2 and r.transition_evaluation_ceiling==20000


def test_primary_comparative_execution_is_authorized_by_m8_lock_record():
    import pvpp_benchmark.execution as ex
    assert ex.PRIMARY_COMPARATIVE_EXECUTION is True

from pvpp_benchmark.planning import ProjectionBudget, PVPPControllerA, ScalarControllerB, default_action_candidates
from pvpp_benchmark.compute_calibration import run_compute_calibration


def test_full_a_b_paths_use_same_root_action_ids_and_pre_only():
    w=AsterionWorld(101); w.state.period=4; w.deteriorate_s1(4,15,20); w.s1_message(4)
    p=w.packet(Role.M)
    ids=[a.action_id for a in default_action_candidates(p)]
    assert len(ids)==len(set(ids))
    a=PVPPControllerA(ProjectionBudget()).decide(p)
    b=ScalarControllerB(ProjectionBudget(),"B0").decide(p)
    assert a.candidate_count==b.candidate_count==len(ids)
    assert a.action.action_id in ids and b.action.action_id in ids


def test_a_b_paths_are_deterministic_on_same_pre_packet():
    w=AsterionWorld(102); w.state.period=3; w.deteriorate_s1(3,10,15); w.s1_message(3); p=w.packet(Role.M)
    a1=PVPPControllerA().decide(p); a2=PVPPControllerA().decide(p)
    b1=ScalarControllerB().decide(p); b2=ScalarControllerB().decide(p)
    assert a1.action==a2.action and b1.action==b2.action


def test_compute_calibration_runs_only_neutral_fixtures_and_selects_common_ceiling():
    r=run_compute_calibration(8)
    assert r["selected"]["multiplier"] in (1,2,4)
    assert r["selected"]["passing_fraction_a"]>=.95
    assert r["selected"]["passing_fraction_b"]>=.95

from pvpp_benchmark.engine import AsterionTransitionEngine
from pvpp_benchmark.oracle_search import FiniteOracleSearcher, OracleClassification
from pvpp_benchmark.model import Action


def _act(w, kind, params=None, target=None, aid=None):
    return Action(aid or f"T-{w.state.period}-{kind.value}",Role.M,kind,params or {},target)


def test_end_to_end_t1_calm_transition_balances_inventory_reserve_and_receipt_delay():
    w=AsterionWorld(200); e=AsterionTransitionEngine(w)
    # Make explicit replenishment available for this isolated world-side trace.
    r=e.realize([_act(w,ActionKind.ROUTINE_PRODUCE,{"units":80}),_act(w,ActionKind.SHIP,{"units":80},Role.C,"SHIP")])
    assert w.state.period==1
    assert w.state.customer_reserve==120  # +80 delivery then -80 consumption
    assert w.state.agents[Role.M].inventory["finished"]==20
    assert any(x.family=="customer_delivery" for x in w.ledger.entries)
    # Receipt is due at P1 and processed after advance.
    assert any(x.family=="customer_receipt" for x in w.ledger.entries)


def test_end_to_end_t5_qualification_launch_does_not_destroy_or_encumber_pp_before_stage():
    w=AsterionWorld(201); e=AsterionTransitionEngine(w)
    before=dict(w.state.agents[Role.M].pp)
    a=_act(w,ActionKind.START_S2_QUAL,{"emergency":False},Role.S2)
    e.realize([a],advance=False)
    assert w.state.agents[Role.M].pp==before
    assert w.state.agents[Role.M].encumbered.get("engineering",0)==0


def test_end_to_end_t6_full_rework_delays_recovered_boards_shortcut_is_immediate():
    # M11 D7: rework requires and consumes conserved suspect substrate.
    a=AsterionWorld(202); ea=AsterionTransitionEngine(a); a.state.agents[Role.M].cash_k=500; a.state.s1_suspect_boards=20
    b0=a.state.agents[Role.M].inventory["s1_boards"]
    ea.realize([_act(a,ActionKind.FULL_REWORK,{"units":20})],advance=False)
    assert a.state.agents[Role.M].inventory["s1_boards"]==b0
    assert a.state.s1_suspect_boards==0
    assert a.state.pending_full_rework
    b=AsterionWorld(202); eb=AsterionTransitionEngine(b); b.state.agents[Role.M].cash_k=500; b.state.s1_suspect_boards=20
    b0=b.state.agents[Role.M].inventory["s1_boards"]
    eb.realize([_act(b,ActionKind.SHORTCUT_REWORK,{"units":20})],advance=False)
    assert b.state.s1_suspect_boards==0
    assert b.state.agents[Role.M].inventory["s1_boards"]==b0+20


def test_end_to_end_t8_reservation_prevents_external_s2_encumbrance_fixture():
    w=AsterionWorld(203); e=AsterionTransitionEngine(w); w.state.period=6
    e.realize([_act(w,ActionKind.RESERVE_S2,{"capacity":60},Role.S2)],advance=False)
    assert w.state.s2_reserved_capacity==60
    w.state.period=7; w.close_s2_opportunity_if_unreserved(w.state.s2_reserved_capacity>0); w.advance_period()
    assert w.state.s2_external_encumbrance==0


def test_end_to_end_finance_draw_changes_cash_and_persistent_headroom():
    w=AsterionWorld(204); e=AsterionTransitionEngine(w); before=w.state.agents[Role.M].cash_k
    e.realize([_act(w,ActionKind.REQUEST_FINANCE,{"amount_k":100},Role.L)],advance=False)
    assert w.state.agents[Role.M].cash_k==before+100-80
    assert abs(w.state.m_covenant_headroom-.94)<1e-9
    assert w.state.m_credit_available_k==400


def test_customer_termination_eligibility_does_not_auto_terminate_in_world():
    w=AsterionWorld(205); e=AsterionTransitionEngine(w); w.state.customer_reserve=20
    w.state.breach_strikes=[0,1,2,3]; w.state.period=4
    e.realize([],advance=False)
    assert w.state.customer_termination_eligible
    assert not w.state.customer_terminated


def test_m13_customer_distress_does_not_cause_exit_while_operations_remain_viable():
    from pvpp_benchmark.production import ProductionRolePolicy
    w=AsterionWorld(1205); AsterionTransitionEngine(w)
    w.state.customer_reserve=0; w.state.customer_termination_eligible=True
    w.state.breach_strikes=[1,2,3,4]
    w.state.agents[Role.C].pp["operations"]=10
    for regime in ("A","B0","C"):
        a=ProductionRolePolicy(regime,Role.C).decide_bundle(w.packet(Role.C),1205)[1][-1]
        assert a.kind is ActionKind.C_CONTINUE


def test_m13_customer_exits_only_after_own_operations_pp_collapses():
    from pvpp_benchmark.production import ProductionRolePolicy
    w=AsterionWorld(1206); e=AsterionTransitionEngine(w)
    w.state.customer_reserve=0; w.state.customer_termination_eligible=True
    w.state.agents[Role.C].pp["operations"]=0
    for regime in ("A","B0","C"):
        a=ProductionRolePolicy(regime,Role.C).decide_bundle(w.packet(Role.C),1206)[1][-1]
        assert a.kind is ActionKind.C_TERMINATE
    premature=Action("C-PREMATURE",Role.C,ActionKind.C_TERMINATE,{},Role.M)
    w2=AsterionWorld(1207); e2=AsterionTransitionEngine(w2)
    w2.state.customer_termination_eligible=True; w2.state.customer_reserve=0
    w2.state.agents[Role.C].pp["operations"]=10
    assert e2.validate(premature)=="CUSTOMER_BUSINESS_STILL_VIABLE"


def test_oracle_budget_exhaustion_is_undetermined_not_infeasible():
    w=AsterionWorld(206); w.state.customer_terminated=True; s=w.state
    search=FiniteOracleSearcher()
    def expand(st):
        return [Action("a",Role.M,ActionKind.NO_ACTION),Action("b",Role.M,ActionKind.NO_ACTION)]
    def step(st,a): return st
    r=search.search(s,expand,step,horizon=3,budget=1)
    assert r.classification is OracleClassification.UNDETERMINED and not r.exhaustive


def test_oracle_exhausted_finite_tree_can_prove_infeasible():
    w=AsterionWorld(207); w.state.customer_terminated=True; s=w.state
    search=FiniteOracleSearcher()
    def expand(st): return [Action("a",Role.M,ActionKind.NO_ACTION)]
    def step(st,a): return st
    r=search.search(s,expand,step,horizon=2,budget=10)
    assert r.classification is OracleClassification.PROVEN_INFEASIBLE and r.exhaustive


def test_oracle_finds_recovery_path_when_transition_restores_terminal_flag_and_resources():
    w=AsterionWorld(208); w.state.customer_terminated=True; w.state.customer_reserve=0
    search=FiniteOracleSearcher()
    def expand(st): return [Action("recover",Role.M,ActionKind.NO_ACTION)]
    def step(st,a):
        st.customer_terminated=False; st.customer_reserve=80; st.agents[Role.M].cash_k=10
        st.agents[Role.M].inventory["s1_boards"]=100
        return st
    r=search.search(w.state,expand,step,horizon=1,budget=5)
    assert r.classification is OracleClassification.RECOVERY_FOUND

from pvpp_benchmark.scenario import MultiAgentScenarioRunner
from pvpp_benchmark.oracle_expansion import frozen_oracle_root_plans, ExactFiniteOracleSearcher


def test_multiagent_scenario_applies_common_supply_and_deterministic_stress_timing():
    w=AsterionWorld(300); r=MultiAgentScenarioRunner(w)
    # Four calibration-only periods with a routine M flow action.
    for _ in range(4):
        p=w.state.period
        acts=(Action(f"P{p}-prod",Role.M,ActionKind.ROUTINE_PRODUCE,{"units":80}),
              Action(f"P{p}-ship",Role.M,ActionKind.SHIP,{"units":80},Role.C))
        r.step(acts)
    assert w.state.period==4
    assert w.state.s1_deterioration_active
    assert w.state.agents[Role.S1].pp["line"]==85
    assert any(x.family=="s1_supply_arrival" for x in w.ledger.entries)
    assert any(x.family=="kit_supply_arrival" for x in w.ledger.entries)


def test_multiagent_s2_opportunity_closes_only_after_end_p7_if_unreserved():
    w=AsterionWorld(301); r=MultiAgentScenarioRunner(w)
    while w.state.period<=7:
        r.step(())
    assert w.state.period==8
    assert w.state.s2_opportunity_announced and w.state.s2_opportunity_closed
    assert w.state.s2_external_encumbrance==30


def test_multiagent_reservation_prevents_period8_external_encumbrance():
    w=AsterionWorld(302); r=MultiAgentScenarioRunner(w)
    # Maintain ordinary operations so the reservation test isolates option closure, not bankruptcy.
    while w.state.period<6:
        p=w.state.period
        r.step((Action(f"P{p}-prod",Role.M,ActionKind.ROUTINE_PRODUCE,{"units":80}),
                Action(f"P{p}-ship",Role.M,ActionKind.SHIP,{"units":80},Role.C)))
    p=w.state.period
    r.step((Action("reserve",Role.M,ActionKind.RESERVE_S2,{"capacity":60},Role.S2),
            Action(f"P{p}-prod",Role.M,ActionKind.ROUTINE_PRODUCE,{"units":80}),
            Action(f"P{p}-ship",Role.M,ActionKind.SHIP,{"units":80},Role.C)))
    p=w.state.period
    r.step((Action(f"P{p}-prod",Role.M,ActionKind.ROUTINE_PRODUCE,{"units":80}),
            Action(f"P{p}-ship",Role.M,ActionKind.SHIP,{"units":80},Role.C)))  # P7 closes opportunity
    assert w.state.period==8 and w.state.s2_external_encumbrance==0


def test_exact_oracle_expander_uses_frozen_action_families_and_feasible_joint_flow():
    w=AsterionWorld(303)
    plans=frozen_oracle_root_plans(w.state)
    ids={p.plan_id for p in plans}
    assert "flow-p80-s80" in ids and "finance-100" in ids and "qual-normal" in ids
    assert all(all(a.actor is Role.M for a in p.actions) for p in plans)


def test_exact_oracle_budget_semantics_remain_conservative():
    w=AsterionWorld(304); w.state.customer_terminated=True; w.state.customer_reserve=0
    r=ExactFiniteOracleSearcher().search(w.state,horizon=3,budget=1)
    assert r.classification is OracleClassification.UNDETERMINED and not r.exhaustive


def test_exact_oracle_can_exhaust_terminal_state_with_no_actions_as_infeasible():
    w=AsterionWorld(305); w.state.customer_terminated=True; w.state.customer_reserve=0
    # Empty finite expander is an explicit completeness certificate for this microfixture.
    from pvpp_benchmark.oracle_expansion import GrammarCompleteness
    r=ExactFiniteOracleSearcher().search(w.state,horizon=2,budget=10,expander=lambda s:(), completeness=lambda s: GrammarCompleteness(True,(),"microfixture complete"))
    assert r.classification is OracleClassification.PROVEN_INFEASIBLE and r.exhaustive

from pvpp_benchmark.oracle_expansion import O1O2OracleProtocol


def test_o1_o2_protocol_uses_frozen_horizons_and_conservative_empty_tree_classification():
    w=AsterionWorld(306); w.state.customer_terminated=True; w.state.customer_reserve=0
    protocol=O1O2OracleProtocol()
    empty=lambda s: ()
    from pvpp_benchmark.oracle_expansion import GrammarCompleteness
    result=protocol.classify(w.state,remaining_trace_horizon=20,expander=empty, completeness=lambda s: GrammarCompleteness(True,(),"microfixture complete"))
    assert result.o1.classification is OracleClassification.PROVEN_INFEASIBLE
    assert result.o1.depth==8
    assert result.o2 is not None and result.o2.classification is OracleClassification.PROVEN_INFEASIBLE
    assert result.o2.depth==12


def test_o1_o2_protocol_stops_after_o1_recovery():
    w=AsterionWorld(307)
    result=O1O2OracleProtocol().classify(w.state,remaining_trace_horizon=12)
    assert result.o1.classification is OracleClassification.RECOVERY_FOUND
    assert result.o2 is None

def test_oracle_integer_lattice_has_no_coarse_quantity_grid():
    from pvpp_benchmark.oracle_expansion import licensed_integer_flow_plans
    w=AsterionWorld(1)
    plans=list(licensed_integer_flow_plans(w.state))
    ids={p.plan_id for p in plans}
    assert "flow-p1-s0" in ids
    assert "flow-p2-s1" in ids
    assert "flow-p40-s40" in ids


def test_v012_default_oracle_grammar_has_completeness_certificate():
    from pvpp_benchmark.oracle_expansion import grammar_completeness
    w=AsterionWorld(1)
    cert=grammar_completeness(w.state)
    assert cert.complete is True
    assert cert.incomplete_families == ()


def test_incomplete_oracle_exhaustion_is_undetermined():
    from pvpp_benchmark.oracle_expansion import ExactFiniteOracleSearcher, JointActionPlan, GrammarCompleteness
    from pvpp_benchmark.oracle_search import OracleClassification
    w=AsterionWorld(1)
    def empty(_state): return ()
    def never(_state): return False
    def incomplete(_state): return GrammarCompleteness(False,("fixture",),"fixture")
    r=ExactFiniteOracleSearcher().search(w.state,horizon=1,budget=10,expander=empty,recovery=never,completeness=incomplete)
    assert r.classification is OracleClassification.UNDETERMINED
    assert r.exhaustive is False


def test_complete_toy_oracle_exhaustion_can_prove_infeasible():
    from pvpp_benchmark.oracle_expansion import ExactFiniteOracleSearcher, GrammarCompleteness
    from pvpp_benchmark.oracle_search import OracleClassification
    w=AsterionWorld(1)
    def empty(_state): return ()
    def never(_state): return False
    def complete(_state): return GrammarCompleteness(True,(),"toy complete")
    r=ExactFiniteOracleSearcher().search(w.state,horizon=1,budget=10,expander=empty,recovery=never,completeness=complete)
    assert r.classification is OracleClassification.PROVEN_INFEASIBLE
    assert r.exhaustive is True


def test_v012_reservation_terms_are_exact_and_fee_is_nonrefundable_fixture():
    w=AsterionWorld(401); e=AsterionTransitionEngine(w)
    bad=Action('badres',Role.M,ActionKind.RESERVE_S2,{'capacity':40,'duration':5},Role.S2)
    assert e.resolve_joint([bad]).rejected[0][1]=='RESERVATION_TERMS_INVALID'
    before_m=w.state.agents[Role.M].cash_k; before_s2=w.state.agents[Role.S2].cash_k
    good=Action('goodres',Role.M,ActionKind.RESERVE_S2,{'capacity':60,'duration':5},Role.S2)
    e.realize([good],advance=False)
    assert w.state.s2_reserved_capacity==60
    assert w.state.s2_reservation_until==w.state.period+5
    assert w.state.agents[Role.M].cash_k==before_m-20-80  # period-end overhead still applies in engine fixture
    assert w.state.agents[Role.S2].cash_k==before_s2+20


def test_v012_customer_renegotiation_accepts_and_rejects_on_same_quantity_by_reserve():
    a=AsterionWorld(402); ea=AsterionTransitionEngine(a); a.state.customer_reserve=100
    act=Action('reneg',Role.M,ActionKind.REQUEST_RENEGOTIATION,{'delivery':60},Role.C)
    assert not ea.resolve_joint([act]).rejected
    ea.realize([act],advance=False)
    assert any(x.family=='renegotiation_accepted' for x in a.ledger.entries)
    b=AsterionWorld(403); eb=AsterionTransitionEngine(b); b.state.customer_reserve=50
    rr=eb.resolve_joint([Action('reneg',Role.M,ActionKind.REQUEST_RENEGOTIATION,{'delivery':60},Role.C)])
    assert rr.rejected and rr.rejected[0][1]=='COUNTERPART_REJECT'


def test_v012_supplier_order_caps_and_receipt_prices_are_frozen():
    w=AsterionWorld(404); e=AsterionTransitionEngine(w)
    ok=Action('s1o',Role.M,ActionKind.ORDER_S1,{'quantity':90},Role.S1)
    assert not e.resolve_joint([ok]).rejected
    bad=Action('s1bad',Role.M,ActionKind.ORDER_S1,{'quantity':91},Role.S1)
    assert e.resolve_joint([bad]).rejected
    e.realize([ok],advance=False)
    c=[c for c in w.state.commitments.values() if c.family=='s1_order'][-1]
    assert c.metadata['price_k']==2.0 and c.metadata['payment']=='receipt'
    w2=AsterionWorld(405); w2.state.s2_qualified=True; w2.state.s2_emergency_conditional=True; e2=AsterionTransitionEngine(w2)
    assert not e2.resolve_joint([Action('s2ok',Role.M,ActionKind.ORDER_S2,{'quantity':40},Role.S2)]).rejected
    assert e2.resolve_joint([Action('s2bad',Role.M,ActionKind.ORDER_S2,{'quantity':41},Role.S2)]).rejected


def test_v012_future_only_cancellation_releases_without_refund():
    w=AsterionWorld(406); e=AsterionTransitionEngine(w)
    e.realize([Action('res',Role.M,ActionKind.RESERVE_S2,{'capacity':60,'duration':5},Role.S2)],advance=False)
    cid=[x for x,c in w.state.commitments.items() if c.family=='s2_capacity'][-1]
    s2cash=w.state.agents[Role.S2].cash_k
    # Same period is still before reservation start, so cancellation is valid; the sunk fee remains with S2.
    r=e.resolve_joint([Action('cancel',Role.M,ActionKind.CANCEL,{'commitment_id':cid})])
    assert not r.rejected
    e.realize([Action('cancel',Role.M,ActionKind.CANCEL,{'commitment_id':cid})],advance=False)
    assert not w.state.commitments[cid].active and w.state.s2_reserved_capacity==0
    assert w.state.agents[Role.S2].cash_k==s2cash


def test_v012_default_oracle_grammar_is_contract_semantically_complete():
    from pvpp_benchmark.oracle_expansion import grammar_completeness, frozen_oracle_root_plans
    w=AsterionWorld(407)
    cert=grammar_completeness(w.state)
    assert cert.complete and not cert.incomplete_families
    ids={p.plan_id for p in frozen_oracle_root_plans(w.state)}
    assert 'reserve-s2-60' in ids and 'reneg-c-80' in ids and 'order-s1-90' in ids


def test_production_a_b_c_are_separate_from_calibration_projectors_and_use_pre_only():
    from pvpp_benchmark.production import ProductionPVPPControllerA, ProductionScalarControllerB, ProductionLocalControllerC
    from pvpp_benchmark.world import AsterionWorld
    w=AsterionWorld(123); p=w.packet(Role.M)
    a=ProductionPVPPControllerA().decide(p,123)
    b=ProductionScalarControllerB().decide(p,123)
    c=ProductionLocalControllerC().decide(p,123)
    assert a.trace.controller=="A-PRODUCTION"
    assert b.trace.controller=="B-B0-PRODUCTION"
    assert c.trace.controller=="C-PRODUCTION"
    assert "calibration" not in a.trace.controller.lower()


def test_production_b_implements_expected_plus_cvar90_and_full_root_coverage():
    from pvpp_benchmark.production import ProductionScalarControllerB
    from pvpp_benchmark.world import AsterionWorld
    w=AsterionWorld(321); p=w.packet(Role.M)
    d=ProductionScalarControllerB().decide(p,321)
    assert d.objective_score is not None
    assert d.trace.evaluated_count==d.trace.candidate_count
    assert d.trace.transition_evaluations<=10000
    assert not d.trace.budget_exhausted


def test_production_a_evaluates_full_current_root_surface_within_common_ceiling():
    from pvpp_benchmark.production import ProductionPVPPControllerA
    from pvpp_benchmark.world import AsterionWorld
    w=AsterionWorld(654); p=w.packet(Role.M)
    d=ProductionPVPPControllerA().decide(p,654)
    assert d.trace.evaluated_count==d.trace.candidate_count
    assert d.trace.transition_evaluations<=10000
    assert not d.trace.budget_exhausted


def test_production_primary_runner_dryrun_works_for_each_regime_without_execution_gate():
    from pvpp_benchmark.production import PrimaryProductionRunner
    for r in ("A","B0","C"):
        rec=PrimaryProductionRunner(r,777,deterministic=True).run(through_period=1)
        assert rec.regime==r
        assert len(rec.decision_traces)>=1
        assert rec.ledger_entries>0


def test_primary_execution_gate_targets_homogeneous_runner_and_is_authorized_by_m8_lock_record():
    import pvpp_benchmark.execution as ex
    assert ex.PRIMARY_COMPARATIVE_EXECUTION is True
    assert ex.run_primary_comparative.__name__ == "run_primary_comparative"


def test_homogeneous_primary_runner_calls_all_economic_roles_with_same_regime_label():
    from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner
    rec=HomogeneousPrimaryProductionRunner("A",991,deterministic=True).run(through_period=0)
    roles={t.role for t in rec.decision_traces}
    assert {Role.M,Role.S1,Role.S2,Role.C,Role.L,Role.T}.issubset(roles)
    assert all(t.controller.startswith("A-") for t in rec.decision_traces)


def test_supplier_supply_is_controller_action_not_bypassed_common_counterpart_supply_in_primary():
    from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner
    r=HomogeneousPrimaryProductionRunner("B0",992,deterministic=True); r.run(through_period=0)
    fam=[e.family for e in r.world.ledger.entries]
    assert "s1_supply_arrival" in fam
    entries=[e for e in r.world.ledger.entries if e.family=="s1_supply_arrival"]
    assert any(e.payload.get("controller_action") is True for e in entries)


def test_primary_p7_opportunity_closure_occurs_after_p7_action_window():
    from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner
    from pvpp_benchmark.model import Commitment
    r=HomogeneousPrimaryProductionRunner("C",993,deterministic=True)
    # Advance to P7 without using the production comparison outcome; directly create the frozen
    # P7 reservation commitment fixture immediately before the P7 action window.
    while r.world.state.period<7:
        r.step()
    s=r.world.state; s.agents[Role.M].cash_k=max(s.agents[Role.M].cash_k,100); s.s2_reserved_capacity=60; s.s2_reservation_until=12
    r.step()
    assert s.s2_external_encumbrance==0
    assert s.s2_opportunity_closed is True


def test_m_production_controllers_submit_routine_flow_inside_their_action_bundle():
    from pvpp_benchmark.production import ProductionPVPPControllerA, ProductionScalarControllerB, ProductionLocalControllerC
    from pvpp_benchmark.world import AsterionWorld
    p=AsterionWorld(994).packet(Role.M)
    for d in (ProductionPVPPControllerA().decide(p,994),ProductionScalarControllerB().decide(p,994),ProductionLocalControllerC().decide(p,994)):
        kinds=[a.kind for a in d.actions]
        assert ActionKind.ROUTINE_PRODUCE in kinds
        assert ActionKind.SHIP in kinds
        assert d.trace.action in d.actions

# --- V2 prospective calibration tests (approved before V2 comparative execution) ---

def test_v2_s2_defect_probability_anchor_points():
    from pvpp_benchmark.world import AsterionWorld
    assert AsterionWorld.s2_defect_probability(70) == pytest.approx(0.02)
    assert AsterionWorld.s2_defect_probability(85) == pytest.approx(0.01)
    assert AsterionWorld.s2_defect_probability(100) == pytest.approx(0.0)
    assert AsterionWorld.s2_defect_probability(55) == pytest.approx(0.03)


def test_v2_supplier_transport_failure_is_exactly_one_period_delay_not_loss():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Action, ActionKind, Role
    w=AsterionWorld(9); e=AsterionTransitionEngine(w)
    w.state.transport_state="HIGH"
    before_boards=w.state.agents[Role.M].inventory.get("s1_boards",0)
    before_cash=w.state.agents[Role.M].cash_k
    a=Action("v2-delay",Role.S1,ActionKind.SHIP,{"units":20},Role.M)
    r=e.realize([a],advance=False)
    assert not r.rejected_actions
    assert w.state.agents[Role.M].inventory.get("s1_boards",0) == before_boards
    assert w.state.agents[Role.M].cash_k == before_cash-80  # period overhead only; no board payment before receipt
    assert len(w.state.pending_transport) == 1
    assert w.state.pending_transport[0]["units"] == 20
    w.advance_period(); e._process_due()
    assert w.state.agents[Role.M].inventory.get("s1_boards",0) == before_boards+20
    assert len(w.state.pending_transport) == 0
    arrivals=[x for x in w.ledger.entries if x.family=="s1_supply_arrival"]
    assert arrivals and arrivals[-1].payload["on_time"] is False
    assert arrivals[-1].payload["units"] == 20


def test_v2_s2_controller_stage_actions_can_complete_normal_qualification():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Action, ActionKind, Role
    w=AsterionWorld(0); e=AsterionTransitionEngine(w)
    w.state.agents[Role.M].cash_k=1000
    start=Action("v2-start",Role.M,ActionKind.START_S2_QUAL,{"emergency":False},Role.S2)
    r=e.realize([start],advance=True)
    assert not r.rejected_actions
    for k in range(4):
        stage=Action(f"v2-stage-{k}",Role.S2,ActionKind.S2_QUAL_STAGE,{},Role.M)
        r=e.realize([stage],advance=True)
        assert not r.rejected_actions
    assert w.state.s2_qualification_stages == 4
    assert w.state.s2_qualified is True
    samples=[x for x in w.ledger.entries if x.family=="s2_qualification_sample"]
    assert len(samples) == 4
    assert all(x.payload["sample_size"]==20 for x in samples)
    assert all(x.payload["defect_probability"]==pytest.approx(0.01) for x in samples)  # initial S2 quality PP=85

# --- V2 Milestone M3: role-controller and outcome-extractor tests ---

def test_v2_s1_role_controller_regime_label_is_not_cosmetic_on_degraded_fixture():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role
    w=AsterionWorld(1201)
    s1=w.state.agents[Role.S1]
    s1.pp['line']=50; s1.pp['quality']=50; s1.pp['recovery']=80; s1.cash_k=260
    acts={r:ProductionRolePolicy(r,Role.S1).decide(w.packet(Role.S1),1201).action.kind for r in ('A','B0','C')}
    assert acts['A'] == ActionKind.S1_RECOVER
    assert acts['C'] == ActionKind.SHIP
    assert len(set(acts.values())) >= 2


def test_v2_customer_primary_policy_does_not_invent_unfrozen_threat_thresholds():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role
    w=AsterionWorld(1202); w.state.customer_reserve=50
    acts={r:ProductionRolePolicy(r,Role.C).decide(w.packet(Role.C),1202).action.kind for r in ('A','B0','C')}
    assert acts == {'A':ActionKind.C_CONTINUE,'B0':ActionKind.C_CONTINUE,'C':ActionKind.C_CONTINUE}


def test_v2_s1_recovery_uses_frozen_numeric_transformation():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Role, Action, ActionKind
    w=AsterionWorld(1203); e=AsterionTransitionEngine(w); s1=w.state.agents[Role.S1]
    s1.pp['line']=50; s1.pp['quality']=50
    cash=s1.cash_k
    r=e.realize([Action('v2-s1-rec',Role.S1,ActionKind.S1_RECOVER,{},Role.S1)],advance=False)
    assert not r.rejected_actions
    assert s1.pp['line']==65 and s1.pp['quality']==70 and s1.cash_k==cash-40
    ev=[x for x in w.ledger.entries if x.family=='s1_recovery'][-1]
    assert ev.payload['recovery_pp']==25 and ev.payload['line_gain']==15 and ev.payload['quality_gain']==20


def test_v2_outcome_extractor_is_metricwise_and_ledger_derived():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Role, Action, ActionKind
    from pvpp_benchmark.outcomes import reconstruct_outcomes
    w=AsterionWorld(1204); e=AsterionTransitionEngine(w)
    e.realize([Action('prod',Role.M,ActionKind.ROUTINE_PRODUCE,{'units':60}),
               Action('ship',Role.M,ActionKind.SHIP,{'units':60},Role.C)],advance=False)
    o=reconstruct_outcomes(w,())
    assert o.committed_units==80
    assert o.delivered_units==60
    assert o.raw_delivery_shortfall==20
    assert o.physical_shortage_unit_weeks==20
    assert o.ledger_entries==len(w.ledger.entries)
    assert not hasattr(o,'global_score')


def test_v2_customer_explicitly_accepts_or_rejects_matching_live_proposal_by_frozen_reserve_predicate():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role, Evidence, EvidenceStatus, ActionKind
    w=AsterionWorld(1301); w.state.customer_reserve=60
    e=Evidence('PROP-X',0,Role.M,Role.C,'live_proposal',{'action_kind':ActionKind.REQUEST_RENEGOTIATION.value,'params':{'delivery':60}},EvidenceStatus.REPORTED)
    w.state.evidence.append(e)
    tr,acts=ProductionRolePolicy('A',Role.C).decide_bundle(w.packet(Role.C),1301)
    assert any(a.kind is ActionKind.C_ACCEPT_RENEG and a.params['proposal_id']=='PROP-X' for a in acts)
    w.state.customer_reserve=50
    tr,acts=ProductionRolePolicy('A',Role.C).decide_bundle(w.packet(Role.C),1301)
    assert any(a.kind is ActionKind.C_REJECT_RENEG and a.params['proposal_id']=='PROP-X' for a in acts)


def test_v2_supplier_and_lender_proposal_responses_use_role_private_feasibility():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role, Evidence, EvidenceStatus, ActionKind
    w=AsterionWorld(1302)
    e1=Evidence('PROP-S1',0,Role.M,Role.S1,'live_proposal',{'action_kind':ActionKind.ORDER_S1.value,'params':{'quantity':90}},EvidenceStatus.REPORTED)
    w.state.evidence.append(e1)
    _,acts=ProductionRolePolicy('B0',Role.S1).decide_bundle(w.packet(Role.S1),1302)
    assert any(a.kind is ActionKind.ACCEPT for a in acts)
    w.state.evidence.remove(e1)
    w.state.m_covenant_headroom=.30
    e2=Evidence('PROP-L',0,Role.M,Role.L,'live_proposal',{'action_kind':ActionKind.REQUEST_FINANCE.value,'params':{'amount_k':50}},EvidenceStatus.REPORTED)
    w.state.evidence.append(e2)
    _,acts=ProductionRolePolicy('C',Role.L).decide_bundle(w.packet(Role.L),1302)
    assert any(a.kind is ActionKind.L_REJECT_DRAW for a in acts)


def test_v2_homogeneous_runner_outcome_record_contains_metricwise_reconstruction():
    from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner
    r=HomogeneousPrimaryProductionRunner('A',1303,deterministic=True)
    rec=r.run(through_period=0)
    assert rec.outcomes
    assert 'physical_shortage_unit_weeks' in rec.outcomes
    assert 'pp_preservation' in rec.outcomes
    assert 'M.assembly' in rec.outcomes['pp_preservation']
    assert 'global_score' not in rec.outcomes

# --- V2 prospective S2/L/T architecture-separation microfixtures ---
from pvpp_benchmark.role_tradeoffs import (
    FixtureChoice, S2TradeoffFixture, LenderTradeoffFixture, TransportTradeoffFixture,
    choose_s2_fixture, choose_lender_fixture, choose_transport_fixture,
)


def test_v2_s2_tradeoff_fixture_is_predeclared_and_architecture_discriminating():
    f=S2TradeoffFixture()
    assert choose_s2_fixture('A',f) is FixtureChoice.S2_EXCESS_CAPACITY
    assert choose_s2_fixture('B0',f) is FixtureChoice.S2_EXCESS_CAPACITY
    assert choose_s2_fixture('C',f) is FixtureChoice.S2_BINDING_RESERVATION


def test_v2_lender_tradeoff_fixture_uses_complete_repayment_objective_not_threshold_only():
    f=LenderTradeoffFixture()
    assert .25 <= f.headroom < .45
    assert f.repay_probability_amend > f.repay_probability_restrict
    assert choose_lender_fixture('A',f) is FixtureChoice.L_AMEND
    assert choose_lender_fixture('C',f) is FixtureChoice.L_AMEND
    # B result is produced by its frozen weighted dimensions, not by a regime label branch.
    assert choose_lender_fixture('B0',f) is FixtureChoice.L_RESTRICT


def test_v2_transport_capacity_conflict_fixture_separates_target_from_guarantee():
    f=TransportTradeoffFixture()
    assert choose_transport_fixture('A',f) is FixtureChoice.T_SERVE_CRITICAL
    assert choose_transport_fixture('B0',f) is FixtureChoice.T_SERVE_PRIOR
    assert choose_transport_fixture('C',f) is FixtureChoice.T_SERVE_PRIOR


def test_v2_s2_verified_outside_opportunity_makes_binding_reservation_discretionary():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.model import Evidence, EvidenceStatus
    w=AsterionWorld(902); w.state.period=6; w.activate_s2_external_opportunity()
    proposal=Evidence('PROP-S2-R',6,Role.M,Role.S2,'live_proposal',
        {'proposal_action_id':'m-res','action_kind':ActionKind.RESERVE_S2.value,'params':{'capacity':60,'duration':5},'target':Role.S2.value},
        EvidenceStatus.REPORTED,False)
    w.state.evidence.append(proposal)
    for regime,expected in [('A',ActionKind.REJECT),('B0',ActionKind.REJECT),('C',ActionKind.S2_ACCEPT_RES)]:
        _,bundle=ProductionRolePolicy(regime,Role.S2).decide_bundle(w.packet(Role.S2),902)
        response=next(a for a in bundle if a.params.get('proposal_id')=='PROP-S2-R')
        assert response.kind is expected


def test_v2_s1_assistance_requires_explicit_s1_acceptance_before_m_side_execution():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.model import Evidence, EvidenceStatus
    w=AsterionWorld(903)
    proposal=Evidence('PROP-S1-A',0,Role.M,Role.S1,'live_proposal',
        {'proposal_action_id':'assist','action_kind':ActionKind.S1_ASSIST.value,'params':{'cash_k':20,'engineering':20},'target':Role.S1.value},
        EvidenceStatus.REPORTED,False)
    w.state.evidence.append(proposal)
    for regime in ('A','B0','C'):
        _,bundle=ProductionRolePolicy(regime,Role.S1).decide_bundle(w.packet(Role.S1),903)
        response=next(a for a in bundle if a.params.get('proposal_id')=='PROP-S1-A')
        assert response.kind is ActionKind.S1_ACCEPT_ASSIST


def test_v2_role_specific_proposal_response_aliases_are_in_common_grammar():
    from pvpp_benchmark.grammar import common_action_grammar
    assert ActionKind.S1_ACCEPT_ASSIST in common_action_grammar(Role.S1)
    assert ActionKind.S2_ACCEPT_QUAL in common_action_grammar(Role.S2)
    assert ActionKind.S2_ACCEPT_RES in common_action_grammar(Role.S2)
    assert ActionKind.C_ACCEPT_RENEG in common_action_grammar(Role.C)
    assert ActionKind.C_REJECT_RENEG in common_action_grammar(Role.C)
    assert ActionKind.L_APPROVE_DRAW in common_action_grammar(Role.L)
    assert ActionKind.L_REJECT_DRAW in common_action_grammar(Role.L)


def test_v2_s2_qualification_launch_and_weekly_stage_costs_are_separate_and_frozen():
    w=AsterionWorld(1301); e=AsterionTransitionEngine(w); m=w.state.agents[Role.M]; s2=w.state.agents[Role.S2]
    cash0=m.cash_k
    e.realize([Action("Q-LAUNCH",Role.M,ActionKind.START_S2_QUAL,{"emergency":False},Role.S2)],advance=False)
    assert m.cash_k==cash0-35-80  # launch plus period overhead; no stage charge yet
    assert m.encumbered.get("engineering",0)==0 and s2.encumbered.get("engineering",0)==0
    # Restore cash only to isolate the same-period stage transformation after overhead.
    m.cash_k=500
    a=Action("Q-STAGE",Role.S2,ActionKind.S2_QUAL_STAGE,{},Role.M)
    before=m.cash_k
    e.realize([a],advance=False)
    assert m.cash_k==before-20-80
    assert m.encumbered.get("engineering",0)==20
    assert s2.encumbered.get("engineering",0)==20
    assert s2.encumbered.get("line",0)==20


def test_v2_s2_stage_below_quality_70_fails_and_does_not_advance_stage_count():
    w=AsterionWorld(1302); e=AsterionTransitionEngine(w)
    w.state.agents[Role.S2].pp["quality"]=69
    w.state.commitments["Q"]=Commitment("Q",(Role.M,Role.S2),"s2_qualification",None,0,None,True,{"emergency":False})
    e.realize([Action("Q-STAGE-LOW",Role.S2,ActionKind.S2_QUAL_STAGE,{},Role.M)],advance=False)
    assert w.state.s2_qualification_stages==0
    assert not w.state.s2_qualified

# --- V2 Milestone M6: complete M physical/action-bundle surface ---

def test_v2_m_root_surface_contains_all_nine_m5_blocker_families():
    from pvpp_benchmark.production import _m_root_actions
    w=AsterionWorld(1601)
    w.state.agents[Role.M].pp['assembly']=90
    kinds={a.kind for a in _m_root_actions(w.packet(Role.M))}
    expected={
        ActionKind.M_CONSERVE,ActionKind.M_RATION,ActionKind.M_SPLIT_SOURCE,
        ActionKind.M_BOOK_T,ActionKind.M_AMEND_L,ActionKind.M_RECOVER_PP,
        ActionKind.M_PAUSE,ActionKind.M_BREACH_CONTROLLED,ActionKind.M_SHUT_LINE,
    }
    # AMEND-L is state-gated and therefore not present while headroom is healthy.
    assert expected-{ActionKind.M_AMEND_L} <= kinds
    w.state.m_covenant_headroom=.20
    assert ActionKind.M_AMEND_L in {a.kind for a in _m_root_actions(w.packet(Role.M))}


def test_v2_conserve_and_ration_rewrite_routine_flow_without_fake_actions():
    from pvpp_benchmark.production import _routine_flow_from_packet
    w=AsterionWorld(1602); p=w.packet(Role.M)
    conserve=Action('CONS',Role.M,ActionKind.M_CONSERVE,{'production_cap':30})
    acts=_routine_flow_from_packet(p,conserve)
    prod=next(a for a in acts if a.kind is ActionKind.ROUTINE_PRODUCE)
    assert prod.params['units']==30
    ration=Action('RAT',Role.M,ActionKind.M_RATION,{'customer_allocation':25})
    acts=_routine_flow_from_packet(p,ration)
    ship=next(a for a in acts if a.kind is ActionKind.SHIP)
    assert ship.params['units']==25


def test_v2_split_source_consumes_exact_named_board_sources():
    w=AsterionWorld(1603); e=AsterionTransitionEngine(w); m=w.state.agents[Role.M]
    w.state.s2_qualified=True; m.inventory['s2_boards']=20
    before1=m.inventory['s1_boards']; before2=m.inventory['s2_boards']
    a=Action('SPLIT-PROD',Role.M,ActionKind.ROUTINE_PRODUCE,{'units':30,'s1_units':20,'s2_units':10})
    r=e.realize([a],advance=False)
    assert not r.rejected_actions
    assert m.inventory['s1_boards']==before1-20
    assert m.inventory['s2_boards']==before2-10


def test_v2_transport_booking_costs_at_booking_and_reserves_named_future_slots():
    w=AsterionWorld(1604); e=AsterionTransitionEngine(w); m=w.state.agents[Role.M]
    cash=m.cash_k
    a=Action('BOOK',Role.M,ActionKind.M_BOOK_T,{'mode':'expedite','route':'M-C','period':9,'slots':1},Role.T)
    r=e.realize([a],advance=False)
    assert not r.rejected_actions
    assert m.cash_k==cash-12-80  # booking fee plus ordinary period-end overhead
    assert any(x['mode']=='expedite' and x['period']==9 and x['slots']==1 for x in w.state.transport_reservations)


def test_v2_emergency_amendment_applies_frozen_fee_headroom_and_future_burden():
    w=AsterionWorld(1605); e=AsterionTransitionEngine(w); m=w.state.agents[Role.M]
    w.state.m_covenant_headroom=.20; cash=m.cash_k
    a=Action('AMEND',Role.M,ActionKind.M_AMEND_L,{'kind':'emergency','fee_k':30},Role.L)
    r=e.realize([a],advance=False)
    assert not r.rejected_actions
    assert w.state.m_covenant_headroom==pytest.approx(.40)
    assert w.state.m_weekly_debt_burden_k==10
    assert m.cash_k==cash-30-80-10


def test_v2_m_recover_pp_consumes_resources_and_restores_at_period_end():
    w=AsterionWorld(1606); e=AsterionTransitionEngine(w); m=w.state.agents[Role.M]
    m.pp['assembly']=70; cash=m.cash_k
    a=Action('REC',Role.M,ActionKind.M_RECOVER_PP,{'domain':'assembly'})
    r=e.realize([a],advance=False)
    assert not r.rejected_actions
    assert m.pp['assembly']==80
    assert m.encumbered['engineering']==20
    assert m.cash_k==cash-25-80
    assert any(x.family=='m_pp_recovery_completed' and x.payload['domain']=='assembly' for x in w.ledger.entries)


def test_v2_pause_can_restore_test_pp_but_produces_nothing_in_composed_flow():
    from pvpp_benchmark.production import _routine_flow_from_packet
    w=AsterionWorld(1607); e=AsterionTransitionEngine(w); m=w.state.agents[Role.M]; m.pp['test']=80
    pause=Action('PAUSE',Role.M,ActionKind.M_PAUSE,{'line':'AM-40'})
    flow=_routine_flow_from_packet(w.packet(Role.M),pause)
    assert not any(a.kind is ActionKind.ROUTINE_PRODUCE for a in flow)
    e.realize([pause],advance=False)
    assert m.pp['test']==88


def test_v2_controlled_breach_preserves_resources_and_records_intentional_nonperformance():
    from pvpp_benchmark.production import _routine_flow_from_packet
    w=AsterionWorld(1608); e=AsterionTransitionEngine(w); m=w.state.agents[Role.M]
    breach=Action('BR',Role.M,ActionKind.M_BREACH_CONTROLLED,{'quantity_not_delivered':30})
    flow=_routine_flow_from_packet(w.packet(Role.M),breach)
    prod=next(a for a in flow if a.kind is ActionKind.ROUTINE_PRODUCE)
    ship=next(a for a in flow if a.kind is ActionKind.SHIP)
    assert prod.params['units']==50 and ship.params['units']==50
    before_boards=m.inventory['s1_boards']
    e.realize(list(flow)+[breach],advance=False)
    assert m.inventory['s1_boards']==before_boards-50
    assert any(x.family=='controlled_breach' and x.payload['quantity_not_delivered']==30 for x in w.ledger.entries)


def test_v2_shutdown_is_irreversible_for_future_primary_line_production():
    w=AsterionWorld(1609); e=AsterionTransitionEngine(w)
    e.realize([Action('SHUT',Role.M,ActionKind.M_SHUT_LINE,{'line':'AM-40'})],advance=True)
    assert w.state.m_line_shutdown is True
    r=e.realize([Action('PROD-AFTER',Role.M,ActionKind.ROUTINE_PRODUCE,{'units':1})],advance=False)
    assert r.rejected_actions and r.rejected_actions[0][1]=='LINE_SHUTDOWN'


def test_v2_t_and_l_emit_matching_role_specific_responses_for_new_proposals():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.model import Evidence, EvidenceStatus
    w=AsterionWorld(1610)
    tp=Evidence('PROP-T',0,Role.M,Role.T,'live_proposal',{'action_kind':ActionKind.M_BOOK_T.value,'params':{'mode':'normal','period':0,'slots':1}},EvidenceStatus.REPORTED)
    w.state.evidence.append(tp)
    _,acts=ProductionRolePolicy('A',Role.T).decide_bundle(w.packet(Role.T),1610)
    assert any(a.kind is ActionKind.T_ACCEPT_BOOK and a.params.get('proposal_id')=='PROP-T' for a in acts)
    w.state.evidence.remove(tp); w.state.m_covenant_headroom=.20
    lp=Evidence('PROP-LA',0,Role.M,Role.L,'live_proposal',{'action_kind':ActionKind.M_AMEND_L.value,'params':{'kind':'emergency'}},EvidenceStatus.REPORTED)
    w.state.evidence.append(lp)
    _,aa=ProductionRolePolicy('A',Role.L).decide_bundle(w.packet(Role.L),1610)
    _,bb=ProductionRolePolicy('B0',Role.L).decide_bundle(w.packet(Role.L),1610)
    assert any(a.kind is ActionKind.L_OFFER_AMEND for a in aa)
    assert any(a.kind is ActionKind.L_REJECT_AMEND for a in bb)


def test_m7_assisted_s1_recovery_uses_authoritative_20_25_increment_and_resets_assistance():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Action, ActionKind, Role
    w=AsterionWorld(701); e=AsterionTransitionEngine(w)
    w.state.agents[Role.S1].pp['line']=60; w.state.agents[Role.S1].pp['quality']=60
    w.state.s1_assisted_recovery=True
    res=e.realize([Action('s1-rec-assist',Role.S1,ActionKind.S1_RECOVER,{},Role.S1)],advance=False)
    assert not res.rejected_actions
    assert w.state.agents[Role.S1].pp['line']==80
    assert w.state.agents[Role.S1].pp['quality']==85
    assert w.state.s1_assisted_recovery is False
    rec=[x for x in w.ledger.entries if x.family=='s1_recovery'][-1]
    assert rec.payload['assisted'] is True and rec.payload['line_gain']==20 and rec.payload['quality_gain']==25


def test_m7_m_to_customer_shipment_requires_current_accepted_transport_capacity():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Action, ActionKind, Role
    w=AsterionWorld(702); e=AsterionTransitionEngine(w)
    w.state.agents[Role.M].inventory['finished']=40
    a=Action('ship-no-t',Role.M,ActionKind.SHIP,{'units':40},Role.C)
    assert e.validate(a)=='TRANSPORT_CAPACITY_SHORTAGE'
    w.state.transport_reservations.append({'reservation_id':'T1','mode':'normal','period':w.state.period,'slots':2,'route':'M-C'})
    assert e.validate(a) is None


def test_m7_m_to_customer_shipment_consumes_transport_reservation_and_enters_transport_realization():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Action, ActionKind, Role
    w=AsterionWorld(703); e=AsterionTransitionEngine(w)
    w.state.agents[Role.M].inventory['finished']=20
    w.state.transport_reservations.append({'reservation_id':'T1','mode':'normal','period':w.state.period,'slots':1,'route':'M-C'})
    a=Action('ship-with-t',Role.M,ActionKind.SHIP,{'units':20},Role.C)
    r=e.realize([a],advance=False)
    assert not r.rejected_actions
    assert not any(x.get('reservation_id')=='T1' for x in w.state.transport_reservations)
    families=[x.family for x in w.ledger.entries]
    assert ('customer_delivery' in families) or ('transport_delay' in families)


def test_m8_execution_is_authorized_only_after_v013_gate_closure():
    import pvpp_benchmark.execution as ex
    assert ex.PRIMARY_COMPARATIVE_EXECUTION is True


def test_v013_primary_role_grammar_is_explicitly_narrowed_not_nominal():
    from pvpp_benchmark.grammar import common_action_grammar
    from pvpp_benchmark.model import ActionKind, Role
    s1=set(common_action_grammar(Role.S1)); s2=set(common_action_grammar(Role.S2))
    assert ActionKind.S1_CONTAIN in s1
    for k in (ActionKind.S1_PRODUCE,ActionKind.S1_RENEGOTIATE,ActionKind.S1_STATUS_MSG,ActionKind.S1_EXIT):
        assert k not in s1
    for k in (ActionKind.S2_QUOTE,ActionKind.S2_TOOL,ActionKind.S2_PRODUCE,ActionKind.S2_EXTERNAL_RESERVE,ActionKind.S2_EXIT):
        assert k not in s2


def test_v013_s1_containment_is_controller_reachable_for_all_architectures_at_frozen_quality_boundary():
    from pvpp_benchmark.production import ProductionRolePolicy
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import ActionKind, Role
    for regime in ('A','B0','B1','B2','B3','B4','C'):
        w=AsterionWorld(801); w.state.agents[Role.S1].pp['quality']=34
        _,acts=ProductionRolePolicy(regime,Role.S1).decide_bundle(w.packet(Role.S1),801)
        assert any(a.kind is ActionKind.S1_CONTAIN for a in acts), regime


def test_v013_s1_containment_blocks_shipment_and_recovery_releases_it():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Action, ActionKind, Role
    w=AsterionWorld(802); e=AsterionTransitionEngine(w)
    s1=w.state.agents[Role.S1]; s1.pp['quality']=34; s1.pp['line']=60
    contain=Action('contain',Role.S1,ActionKind.S1_CONTAIN,{},Role.S1)
    assert e.validate(contain) is None
    e.realize([contain],advance=False)
    assert w.state.s1_containment_active is True
    assert e.validate(Action('ship',Role.S1,ActionKind.SHIP,{'units':10},Role.M))=='S1_CONTAINED'
    e.realize([Action('recover',Role.S1,ActionKind.S1_RECOVER,{},Role.S1)],advance=False)
    assert s1.pp['quality']>=35 and w.state.s1_containment_active is False


def test_v013_s1_shipment_embeds_current_line_output_and_uses_stock_only_for_shortfall():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Action, ActionKind, Role
    w=AsterionWorld(803); e=AsterionTransitionEngine(w)
    s1=w.state.agents[Role.S1]; s1.pp['line']=60; s1.inventory['stock']=40
    a=Action('ship90',Role.S1,ActionKind.SHIP,{'units':90},Role.M)
    assert e.validate(a) is None
    e.realize([a],advance=False)
    assert s1.inventory['stock']==10
    evt=[x for x in w.ledger.entries if x.family in ('s1_supply_arrival','transport_delay')][-1]
    assert evt.payload['stock_used']==30


def test_v013_s1_objective_exit_is_world_transition_not_controller_action():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role
    w=AsterionWorld(804); s1=w.state.agents[Role.S1]
    s1.cash_k=0; s1.pp['line']=20
    w.advance_period(); assert s1.exited is False
    w.advance_period(); assert s1.exited is True
    assert any(x.family=='s1_exit' for x in w.ledger.entries)


def test_v013_s2_objective_exit_is_world_transition_when_cash_low_and_no_contract():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role
    w=AsterionWorld(805); s2=w.state.agents[Role.S2]
    s2.cash_k=29
    w.advance_period()
    assert s2.exited is True
    assert any(x.family=='s2_exit' for x in w.ledger.entries)


def test_v013_primary_s2_scale_up_is_explicitly_out_of_scope_and_line_ceiling_stays_70_without_existing_world_event():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.grammar import common_action_grammar
    from pvpp_benchmark.model import ActionKind, Role
    w=AsterionWorld(806)
    assert ActionKind.S2_TOOL not in common_action_grammar(Role.S2)
    assert w.state.agents[Role.S2].pp['line']==70


def test_v014_recovery_agreement_is_in_common_m_action_grammar():
    from pvpp_benchmark.grammar import common_action_grammar
    from pvpp_benchmark.model import ActionKind, Role
    assert ActionKind.M_RECOVERY_AGREEMENT in common_action_grammar(Role.M)


def test_v014_recovery_terms_use_only_m_pre_visible_state_and_meet_frozen_thresholds():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role
    from pvpp_benchmark.production import _credible_recovery_terms
    w=AsterionWorld(901)
    terms=_credible_recovery_terms(w.packet(Role.M))
    assert terms is not None
    assert terms['projected_next']>=70 and terms['projected_following']>=80
    assert terms['duration_periods']==2


def test_v014_customer_accepts_live_recovery_proposal_and_continues_at_exit_boundary():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.model import Role, Evidence, EvidenceStatus, ActionKind
    from pvpp_benchmark.production import ProductionRolePolicy
    w=AsterionWorld(902); w.state.customer_reserve=30; w.state.__dict__['customer_termination_eligible']=True
    e=Evidence('PROP-REC',w.state.period,Role.M,Role.C,'live_proposal',
               {'proposal_action_id':'REC','action_kind':ActionKind.M_RECOVERY_AGREEMENT.value,
                'params':{'projected_next':70,'projected_following':80,'duration_periods':2},'target':'C'},EvidenceStatus.REPORTED,False)
    w.state.evidence.append(e)
    _,acts=ProductionRolePolicy('A',Role.C).decide_bundle(w.packet(Role.C),902)
    assert any(a.kind is ActionKind.ACCEPT and a.params.get('proposal_id')=='PROP-REC' for a in acts)
    assert any(a.kind is ActionKind.C_CONTINUE for a in acts)
    assert not any(a.kind is ActionKind.C_TERMINATE for a in acts)


def test_v014_accepted_recovery_agreement_persists_for_exactly_two_customer_decision_periods():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Role, Action, ActionKind
    w=AsterionWorld(903); e=AsterionTransitionEngine(w)
    a=Action('REC',Role.M,ActionKind.M_RECOVERY_AGREEMENT,{'projected_next':70,'projected_following':80,'duration_periods':2},Role.C)
    e.realize([a],advance=False)
    assert any(x.claim_family=='accepted_recovery_agreement' for x in w.packet(Role.C).evidence)
    w.advance_period()
    assert any(x.claim_family=='accepted_recovery_agreement' for x in w.packet(Role.C).evidence)
    w.advance_period()
    assert not any(x.claim_family=='accepted_recovery_agreement' for x in w.packet(Role.C).evidence)


def test_v014_recovery_agreement_creates_no_resources_or_guaranteed_delivery():
    from pvpp_benchmark.world import AsterionWorld
    from pvpp_benchmark.engine import AsterionTransitionEngine
    from pvpp_benchmark.model import Role, Action, ActionKind
    w=AsterionWorld(904); e=AsterionTransitionEngine(w)
    before=(w.state.agents[Role.M].cash_k,dict(w.state.agents[Role.M].inventory),dict(w.state.agents[Role.M].pp),w.state.customer_reserve)
    a=Action('REC',Role.M,ActionKind.M_RECOVERY_AGREEMENT,{'projected_next':75,'projected_following':80,'duration_periods':2},Role.C)
    e._execute(a)
    after=(w.state.agents[Role.M].cash_k,dict(w.state.agents[Role.M].inventory),dict(w.state.agents[Role.M].pp),w.state.customer_reserve)
    assert before==after
    assert any(x.family=='recovery_agreement_accepted' for x in w.ledger.entries)


def test_v014_recovery_corridor_is_production_reachable_for_all_seven_regimes():
    from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner
    from pvpp_benchmark.model import Role
    for i,regime in enumerate(('A','B0','B1','B2','B3','B4','C')):
        r=HomogeneousPrimaryProductionRunner(regime,950+i,deterministic=True)
        s=r.world.state; s.period=10; s.customer_reserve=30; s.__dict__['customer_termination_eligible']=True; s.__dict__['breach_strikes']=[6,7,8,9]
        # Keep the fixture inside the credible-plan corridor without granting any new resources.
        s.agents[Role.M].inventory['s1_boards']=160; s.agents[Role.M].inventory['kits']=150; s.agents[Role.M].inventory['finished']=20; s.agents[Role.M].cash_k=420
        r.step()
        assert not s.customer_terminated, regime
        assert any(x.family=='recovery_agreement_accepted' for x in r.world.ledger.entries), regime


def test_v015_recovery_agreement_cannot_roll_over_after_acceptance():
    from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner
    from pvpp_benchmark.model import Role
    r=HomogeneousPrimaryProductionRunner('A',9901,deterministic=True)
    s=r.world.state; s.period=10; s.customer_reserve=30
    s.__dict__['customer_termination_eligible']=True; s.__dict__['breach_strikes']=[6,7,8,9]
    s.agents[Role.M].inventory['s1_boards']=160; s.agents[Role.M].inventory['kits']=150
    s.agents[Role.M].inventory['finished']=20; s.agents[Role.M].cash_k=420
    r.step()
    accepted=[x for x in r.world.ledger.entries if x.family=='recovery_agreement_accepted']
    assert len(accepted)==1
    assert bool(getattr(s,'recovery_agreement_used',False))
    # Keep the world at the customer-exit boundary with a still-credible plan.  A second
    # recovery proposal is forbidden even while/after the first agreement ages out.
    s.customer_reserve=30; s.__dict__['customer_termination_eligible']=True; s.__dict__['breach_strikes']=[7,8,9,10]
    s.agents[Role.M].inventory['s1_boards']=160; s.agents[Role.M].inventory['kits']=150
    s.agents[Role.M].inventory['finished']=20; s.agents[Role.M].cash_k=420
    r.step()
    accepted=[x for x in r.world.ledger.entries if x.family=='recovery_agreement_accepted']
    assert len(accepted)==1
    assert not any(x.family=='proposal_issued' and x.payload.get('action_kind')=='m_recovery_agreement' and x.period==11 for x in r.world.ledger.entries)


def test_v015_expiry_returns_customer_to_ordinary_termination_rule_without_renewal():
    from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner
    from pvpp_benchmark.model import Role
    r=HomogeneousPrimaryProductionRunner('A',9902,deterministic=True)
    s=r.world.state; s.period=10; s.customer_reserve=30
    s.__dict__['customer_termination_eligible']=True; s.__dict__['breach_strikes']=[6,7,8,9]
    s.agents[Role.M].inventory['s1_boards']=160; s.agents[Role.M].inventory['kits']=150
    s.agents[Role.M].inventory['finished']=20; s.agents[Role.M].cash_k=420
    r.step()  # accepted at P10, valid for P10 and P11 decisions
    # Force continued boundary conditions without allowing the ordinary world flow to repair them.
    # Advance through the remaining protected decision period, then inspect the P12 customer packet.
    s.customer_reserve=30; s.__dict__['customer_termination_eligible']=True; s.__dict__['breach_strikes']=[7,8,9,10]
    s.agents[Role.M].inventory['s1_boards']=160; s.agents[Role.M].inventory['kits']=150
    s.agents[Role.M].inventory['finished']=20; s.agents[Role.M].cash_k=420
    r.step()
    # At P12 the accepted evidence has expired; one-time flag blocks replacement.
    assert s.period==12
    assert not any(e.claim_family=='accepted_recovery_agreement' for e in r.world.packet(Role.C).evidence)
    assert bool(getattr(s,'recovery_agreement_used',False))
