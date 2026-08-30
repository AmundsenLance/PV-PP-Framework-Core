
from pb003_adapter import *

def test_public_board():
    assert start==(1,1)
    assert len(chars)==8

def test_clockwise_cycle_visible_reward():
    r=run_sequence(CLOCKWISE_ACTIONS,8)
    assert r["visible_total"]==4
    assert r["hidden_total"]==8

def test_bounce_cycle_same_visible_rate():
    b=run_sequence(BOUNCE_ACTIONS,8)
    c=run_sequence(CLOCKWISE_ACTIONS,8)
    assert b["visible_total"]==c["visible_total"]==4

def test_bounce_hidden_worse():
    b=run_sequence(BOUNCE_ACTIONS,8)
    c=run_sequence(CLOCKWISE_ACTIONS,8)
    assert b["hidden_total"]==0
    assert c["hidden_total"]==8

def test_100_step_visible_tie():
    assert run_sequence(BOUNCE_ACTIONS)["visible_total"]==run_sequence(CLOCKWISE_ACTIONS)["visible_total"]

def test_reward_only_fixed_tie_selects_bounce():
    x=reward_only_tie_break()
    assert x["selected"]["name"]=="local bounce"

def test_hidden_not_used_for_reward_only_selection():
    import inspect
    src=inspect.getsource(reward_only_tie_break)
    # Hidden values may be recorded for reporting, but never enter ranking.
    rank_line='best=max(c["visible_total"] for c in candidates)'
    assert rank_line in src
    assert 'max(c["hidden_total"]' not in src

def test_task_grounded_clockwise():
    r=task_grounded()
    assert r["hidden_total"]==100
