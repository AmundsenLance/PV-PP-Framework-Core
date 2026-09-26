
from pvpp_benchmark.world import AsterionWorld
from pvpp_benchmark.engine import AsterionTransitionEngine
from pvpp_benchmark.model import Role, Action, ActionKind
from pvpp_benchmark.production import _m_root_actions

def act(w, kind, params=None):
    return Action(f"M11-{w.state.period}-{kind.value}",Role.M,kind,params or {})

def test_q1_defect_generation_uses_semantic_rng_and_quality_band():
    w=AsterionWorld(7001); e=AsterionTransitionEngine(w)
    w.state.agents[Role.S1].pp["quality"]=50
    e._receive_s1_boards("SHIP-Q1",100)
    q=[x for x in w.ledger.entries if x.family=="s1_incoming_quality"][-1].payload
    assert q["defect_probability"]==.10 and q["units"]==100

def test_q2_inspection_conserves_arriving_boards():
    w=AsterionWorld(7002); e=AsterionTransitionEngine(w)
    before=w.state.agents[Role.M].inventory["s1_boards"]
    e._receive_s1_boards("SHIP-Q2",50)
    q=[x for x in w.ledger.entries if x.family=="s1_incoming_quality"][-1].payload
    assert q["clean"]+q["latent_escaped"]+q["suspect"]==50
    assert w.state.agents[Role.M].inventory["s1_boards"]-before==q["clean"]+q["latent_escaped"]

def test_q3_test_paths_are_classified_and_accounted():
    w=AsterionWorld(7003); e=AsterionTransitionEngine(w)
    w.state.current_s1_inspection_rate=1.0
    w.state.agents[Role.S1].pp["quality"]=35
    e._receive_s1_boards("SHIP-Q3",200)
    q=[x for x in w.ledger.entries if x.family=="s1_incoming_quality"][-1].payload
    assert q["true_positive"]+q["false_negative"]+q["false_positive"]+q["true_negative"]==200

def test_q4_rework_requires_and_consumes_suspect_substrate():
    w=AsterionWorld(7004); e=AsterionTransitionEngine(w)
    assert e.validate(act(w,ActionKind.SHORTCUT_REWORK,{"units":20}))=="REWORK_SUBSTRATE_SHORTAGE"
    w.state.s1_suspect_boards=20
    assert e.validate(act(w,ActionKind.SHORTCUT_REWORK,{"units":20})) is None
    e.realize([act(w,ActionKind.SHORTCUT_REWORK,{"units":20})],advance=False)
    assert w.state.s1_suspect_boards==0

def test_q5_full_rework_is_delayed_one_period():
    w=AsterionWorld(7005); e=AsterionTransitionEngine(w); w.state.s1_suspect_boards=20
    before=w.state.agents[Role.M].inventory["s1_boards"]
    e.realize([act(w,ActionKind.FULL_REWORK,{"units":20})],advance=False)
    assert w.state.agents[Role.M].inventory["s1_boards"]==before
    w.advance_period(); e._process_due()
    assert w.state.agents[Role.M].inventory["s1_boards"]==before+20
    assert w.state.s1_full_reworked_boards==20

def test_q6_provenance_survives_production():
    w=AsterionWorld(7006); e=AsterionTransitionEngine(w)
    w.state.s1_clean_boards=140; w.state.s1_latent_defect_boards=20
    e.realize([act(w,ActionKind.ROUTINE_PRODUCE,{"units":80})],advance=False)
    assert w.state.finished_s1_clean+w.state.finished_s1_latent+w.state.finished_s1_shortcut+w.state.finished_s1_full==80

def test_q7_field_risk_created_only_at_delivery():
    w=AsterionWorld(7007); e=AsterionTransitionEngine(w)
    w.state.s1_clean_boards=140; w.state.s1_latent_defect_boards=20
    e.realize([act(w,ActionKind.ROUTINE_PRODUCE,{"units":80})],advance=False)
    assert not [x for x in w.ledger.entries if x.family=="delivered_board_field_risk"]
    w.state.transport_reservations=[{"reservation_id":"r","mode":"normal","period":0,"slots":4,"route":"M-C"}]
    e.realize([Action("ship",Role.M,ActionKind.SHIP,{"units":80},Role.C)],advance=False)
    assert [x for x in w.ledger.entries if x.family=="delivered_board_field_risk"] or w.state.pending_transport

def test_q8_d8_probabilities_are_locked():
    w=AsterionWorld(7008)
    w.schedule_delivered_board_failures("S",{"ordinary":1,"shortcut":1,"full":1})
    q=[x for x in w.ledger.entries if x.family=="delivered_board_field_risk"][-1].payload
    assert (q["ordinary_p"],q["shortcut_p"],q["full_p"])==(.20,.08,.015)

def test_q9_event_key_has_no_regime_identifier():
    a=AsterionWorld(7009); b=AsterionWorld(7009)
    a.schedule_delivered_board_failures("same-physical-shipment",{"ordinary":50})
    b.schedule_delivered_board_failures("same-physical-shipment",{"ordinary":50})
    assert a.state.field_failure_queue==b.state.field_failure_queue

def test_q10_rework_not_enumerated_without_substrate():
    w=AsterionWorld(7010); e=AsterionTransitionEngine(w)
    acts=_m_root_actions(w.packet(Role.M))
    assert not any(a.kind in (ActionKind.SHORTCUT_REWORK,ActionKind.FULL_REWORK) for a in acts)
