from pvpp_benchmark.world import AsterionWorld
from pvpp_benchmark.engine import AsterionTransitionEngine
from pvpp_benchmark.model import Role, Action, ActionKind


def act(w, kind, params=None, target=None, aid=None):
    return Action(aid or f"M12-{w.state.period}-{kind.value}", Role.M, kind, params or {}, target)


def test_d9_fifo_usable_inventory_ignores_hidden_provenance():
    w=AsterionWorld(8101); e=AsterionTransitionEngine(w); s=w.state; m=s.agents[Role.M]
    # Replace initial stock with an explicit receipt-order queue: latent first, clean second.
    m.inventory["s1_boards"]=40
    s.s1_usable_cohorts=[
        {"source":"old","period":0,"provenance":"latent","units":20.0},
        {"source":"new","period":1,"provenance":"clean","units":20.0},
    ]
    s.s1_clean_boards=20; s.s1_latent_defect_boards=20
    s.s1_shortcut_reworked_boards=0; s.s1_full_reworked_boards=0
    m.inventory["kits"]=100; m.cash_k=1000
    e.realize([act(w,ActionKind.ROUTINE_PRODUCE,{"units":20,"s1_units":20,"s2_units":0})],advance=False)
    assert s.finished_s1_latent==20
    assert s.finished_s1_clean==0
    assert s.s1_usable_cohorts[0]["provenance"]=="clean"


def test_d9_fifo_result_changes_with_receipt_order_not_quality_priority():
    w=AsterionWorld(8102); e=AsterionTransitionEngine(w); s=w.state; m=s.agents[Role.M]
    m.inventory["s1_boards"]=40
    s.s1_usable_cohorts=[
        {"source":"old","period":0,"provenance":"clean","units":20.0},
        {"source":"new","period":1,"provenance":"latent","units":20.0},
    ]
    s.s1_clean_boards=20; s.s1_latent_defect_boards=20
    s.s1_shortcut_reworked_boards=0; s.s1_full_reworked_boards=0
    m.inventory["kits"]=100; m.cash_k=1000
    e.realize([act(w,ActionKind.ROUTINE_PRODUCE,{"units":20,"s1_units":20,"s2_units":0})],advance=False)
    assert s.finished_s1_clean==20
    assert s.finished_s1_latent==0


def test_d9_rework_output_appends_to_fifo_tail():
    w=AsterionWorld(8103); e=AsterionTransitionEngine(w); s=w.state; m=s.agents[Role.M]
    s.s1_suspect_boards=20; m.cash_k=1000
    before_sources=[c["source"] for c in s.s1_usable_cohorts]
    e.realize([act(w,ActionKind.SHORTCUT_REWORK,{"units":20},aid="RW")],advance=False)
    assert s.s1_usable_cohorts[-1]["source"]=="RW"
    assert s.s1_usable_cohorts[-1]["provenance"]=="shortcut"
    assert [c["source"] for c in s.s1_usable_cohorts[:-1]]==before_sources


def test_d9_finished_goods_shipping_is_fifo_not_risk_priority():
    w=AsterionWorld(8104); e=AsterionTransitionEngine(w); s=w.state; m=s.agents[Role.M]
    m.inventory["finished"]=40
    s.finished_s1_cohorts=[
        {"source":"prod-old","period":0,"provenance":"latent","units":20.0},
        {"source":"prod-new","period":1,"provenance":"clean","units":20.0},
    ]
    s.finished_s1_latent=20; s.finished_s1_clean=20
    s.transport_reservations=[{"reservation_id":"r","mode":"normal","period":0,"slots":1,"route":"M-C"}]
    e.realize([act(w,ActionKind.SHIP,{"units":20},Role.C,aid="SHIP")],advance=False)
    # Whether delivered immediately or delayed, the shipped provenance must be the oldest latent cohort.
    risk_entries=[x for x in w.ledger.entries if x.family=="delivered_board_field_risk"]
    if risk_entries:
        assert risk_entries[-1].payload["risk_counts"]["ordinary"]==20
    else:
        assert s.pending_transport[-1]["risk_provenance"]["ordinary"]==20
    assert s.finished_s1_cohorts[0]["provenance"]=="clean"


def test_d9_fifo_conserves_usable_queue_and_aggregate_inventory():
    w=AsterionWorld(8105); e=AsterionTransitionEngine(w); s=w.state; m=s.agents[Role.M]
    e._receive_s1_boards("ARR",90)
    assert abs(sum(c["units"] for c in s.s1_usable_cohorts)-m.inventory["s1_boards"])<1e-9
