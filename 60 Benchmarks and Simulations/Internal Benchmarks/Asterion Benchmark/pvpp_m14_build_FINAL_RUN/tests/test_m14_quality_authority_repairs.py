from pvpp_benchmark.world import AsterionWorld, ConformanceError
from pvpp_benchmark.engine import AsterionTransitionEngine
from pvpp_benchmark.model import Role


def incoming_payload(w):
    return [x for x in w.ledger.entries if x.family=="s1_incoming_quality"][-1].payload


def test_d10_rolling_two_week_delivery_cohort_triggers_across_due_periods():
    w=AsterionWorld(14001); e=AsterionTransitionEngine(w); s=w.state
    # Two failures attributable to delivery P2 become visible in P5.
    s.period=5
    s.field_failure_queue=[
        {"batch":"A","board_id":"A1","delivery_period":2,"due":5,"provenance":"ordinary"},
        {"batch":"A","board_id":"A2","delivery_period":2,"due":5,"provenance":"ordinary"},
        {"batch":"B","board_id":"B1","delivery_period":3,"due":6,"provenance":"ordinary"},
        {"batch":"B","board_id":"B2","delivery_period":3,"due":6,"provenance":"ordinary"},
    ]
    e._process_due()
    assert s.major_field_events==0
    s.period=6; e._process_due()
    assert s.major_field_events==1
    ev=[x for x in w.ledger.entries if x.family=="major_field_quality_event"][-1]
    assert tuple(ev.payload["delivery_window"])==(2,3)
    assert ev.payload["failures"]==4


def test_d10_nonadjacent_delivery_failures_do_not_form_major_event():
    w=AsterionWorld(14002); e=AsterionTransitionEngine(w); s=w.state
    s.period=6
    s.field_failure_queue=[
        {"batch":"A","board_id":"A1","delivery_period":1,"due":6,"provenance":"ordinary"},
        {"batch":"A","board_id":"A2","delivery_period":1,"due":6,"provenance":"ordinary"},
        {"batch":"B","board_id":"B1","delivery_period":4,"due":6,"provenance":"ordinary"},
        {"batch":"B","board_id":"B2","delivery_period":4,"due":6,"provenance":"ordinary"},
    ]
    e._process_due()
    assert s.major_field_events==0


def test_inspection_is_event_keyed_uniform_subset_without_replacement():
    a=AsterionWorld(14003); b=AsterionWorld(14003)
    ea=AsterionTransitionEngine(a); eb=AsterionTransitionEngine(b)
    a.state.current_s1_inspection_rate=b.state.current_s1_inspection_rate=.20
    ea._receive_s1_boards("SAME-SHIP",20,shipment_quality_pp=80)
    eb._receive_s1_boards("SAME-SHIP",20,shipment_quality_pp=80)
    pa=incoming_payload(a); pb=incoming_payload(b)
    assert pa["sample_size"]==5
    assert pa["sampled_board_ids"]==pb["sampled_board_ids"]
    assert len(set(pa["sampled_board_ids"]))==5
    assert set(pa["sampled_board_ids"]) != {f"SAME-SHIP:board:{i}" for i in range(5)}


def test_inspection_rate_closure_uses_ceiling_to_meet_frozen_percentage():
    w=AsterionWorld(14004); e=AsterionTransitionEngine(w)
    w.state.current_s1_inspection_rate=.50
    e._receive_s1_boards("ODD-SHIP",21,shipment_quality_pp=80)
    assert incoming_payload(w)["sample_size"]==11


def test_s1_quality_below_35_has_no_invented_defect_probability_branch():
    w=AsterionWorld(14005); e=AsterionTransitionEngine(w)
    try:
        e._receive_s1_boards("INVALID",20,shipment_quality_pp=34)
    except ConformanceError:
        pass
    else:
        raise AssertionError("quality <35 must not invent a defect probability")


def test_delayed_arrival_uses_quality_at_valid_shipment_not_later_quality():
    w=AsterionWorld(14006); e=AsterionTransitionEngine(w)
    w.state.agents[Role.S1].pp["quality"]=20
    e._receive_s1_boards("IN-TRANSIT",20,shipment_quality_pp=40)
    p=incoming_payload(w)
    assert p["quality_pp"]==40
    assert p["defect_probability"]==.20


def test_field_crn_follows_stable_board_identity_not_final_shipment_ordinal():
    a=AsterionWorld(14007); b=AsterionWorld(14007)
    a.state.period=b.state.period=4
    ids=[f"PHYSICAL-{i}" for i in range(100)]
    a.schedule_delivered_board_failures("CUSTOMER-SHIP-A",{"ordinary":ids})
    b.schedule_delivered_board_failures("CUSTOMER-SHIP-B",{"ordinary":ids})
    av=[(q["board_id"],q["due"],q["provenance"]) for q in a.state.field_failure_queue]
    bv=[(q["board_id"],q["due"],q["provenance"]) for q in b.state.field_failure_queue]
    assert av==bv


def test_p16_customer_collapse_is_reported_as_right_censored_not_survival():
    from pvpp_benchmark.outcomes import reconstruct_outcomes
    w=AsterionWorld(14008); AsterionTransitionEngine(w)
    w.state.agents[Role.C].pp["operations"]=0
    w.state.customer_terminated=False
    out=reconstruct_outcomes(w)
    assert out.customer_business_collapse is True
    assert out.customer_collapse_right_censored is True
    assert out.customer_terminated is False
