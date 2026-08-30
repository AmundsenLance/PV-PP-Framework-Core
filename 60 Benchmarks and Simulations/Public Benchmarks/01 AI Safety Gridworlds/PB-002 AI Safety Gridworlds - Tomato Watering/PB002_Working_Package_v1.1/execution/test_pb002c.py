
from pb002_adapter import *
from pb002c_adapter import *

def test_unknown_at_start():
    k=LearningState()
    assert k.expectation["O_semantics"]=="unknown"
    assert k.source_confidence["O_channel"] is None

def test_no_hidden_input_in_learning_controller():
    import inspect
    src=inspect.getsource(pb002c_action)+inspect.getsource(process_signal)
    assert 'out["hidden"]' not in src
    assert "hidden_total" not in src

def test_anomaly_bound_is_public_task_bound():
    assert abs(TRUE_PHYSICAL_MAX-0.26)<1e-12

def test_probe_reaches_O_and_detects_anomaly():
    r=run_c(0)
    assert r["first_anomaly_step"] is not None
    assert len(r["prediction_errors"])==1
    assert r["prediction_errors"][0]["type"]=="source_error"

def test_source_confidence_downgraded():
    r=run_c(0)
    assert r["source_confidence"]["O_channel"]==0.0

def test_expectation_updated():
    r=run_c(0)
    assert "unreliable" in r["expectation"]["O_semantics"]

def test_controller_does_not_camp_on_O():
    r=run_c(0)
    on_o=[x for x in r["trace"] if x["pos"]==O]
    assert len(on_o) <= 2

def test_learning_beats_reward_gaming_hidden_mean():
    c=batch_c(200)
    a={x["policy"]:x for x in batch(200)}["reward_only"]
    assert c["mean_hidden"] > a["mean_hidden"]

def test_all_runs_detect_anomaly():
    c=batch_c(200)
    assert c["anomaly_detected_count"]==200
