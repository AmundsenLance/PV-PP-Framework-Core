
from pb005_adapter import *

def test_training_relation_perfect():
    r=run()["training"]
    assert r["contradictions"]==0 and r["A_good"]==100 and r["B_bad"]==100

def test_same_initial_expectation():
    a=Learner(True); f=Learner(False)
    assert a.expectation==f.expectation and a.confidence==f.confidence

def test_first_eval_action_same():
    a=Learner(True); f=Learner(False)
    assert a.choose("A")==f.choose("A")=="use"

def test_first_shift_event_causes_prediction_error():
    a=Learner(True)
    e=evaluation_episode(a)
    assert e["harm"] and len(a.errors)==1

def test_error_typed():
    a=Learner(True); evaluation_episode(a)
    assert a.errors[0]["type"]=="policy_outcome_error"

def test_local_confidence_update():
    a=Learner(True); evaluation_episode(a)
    assert a.confidence["appearance_channel"]==0.0

def test_expectation_updated_not_actual_rewritten():
    a=Learner(True); evaluation_episode(a)
    assert a.expectation["A"]=="unreliable_in_current_context"

def test_adaptive_stops_repeating_harm():
    r=run()["adaptive"]
    assert r["harms"]==1
    assert all(e["action"]=="bypass" for e in r["episodes"][1:])

def test_frozen_repeats_harm():
    r=run()["frozen"]
    assert r["harms"]==20

def test_adaptive_outperforms_frozen_after_shift():
    r=run()
    assert r["adaptive"]["total_reward"] > r["frozen"]["total_reward"]

def test_no_hidden_evaluator_in_learner():
    import inspect
    src=inspect.getsource(Learner)
    assert "hidden" not in src.lower()
    assert "performance" not in src.lower()
