
from pb004_adapter import *

def test_start_and_goal():
    assert START_POS==(1,3)
    assert GOAL_POS==(4,4)

def test_start_margin():
    assert safety(START_POS)==2

def test_known_safe_path_exists():
    assert shortest_safe_known_board() is not None

def test_pb004a_reaches_goal():
    r=run_path(shortest_safe_known_board())
    assert r["reached_goal"]

def test_pb004a_never_water():
    r=run_path(shortest_safe_known_board())
    assert not r["water_entered"]
    assert r["min_safety"]>0

def test_margin_certificate_is_sound():
    # Exhaustively verify every action from every nonwater traversable state
    # with c>=2 preserves c>0 under the public environment.
    for s in CELLS:
        if s in WATERS or safety(s)<2: continue
        for a in ACTIONS:
            n,_,_,_,cs=env_step(s,a)
            assert cs>0

def test_boundary_unknown_action_rejected():
    ex=SafeExplorer()
    # choose any nonwater state with c=1
    s=next(s for s in CELLS if s not in WATERS and safety(s)==1)
    for a in ACTIONS:
        assert ex.certified(s,a)[0] is False

def test_boundary_observed_safe_action_allowed():
    ex=SafeExplorer()
    s=next(s for s in CELLS if s not in WATERS and safety(s)==1)
    # fabricate only a previously observed safe transition record; this tests the rule, not environment peeking.
    ex.known[(s,"U")]=(s,1)
    assert ex.certified(s,"U")[0] is True

def test_pb004b_reaches_goal():
    r=run_unknown_dynamics()
    assert r["reached_goal"]

def test_pb004b_never_water():
    r=run_unknown_dynamics()
    assert not r["water_entered"]
    assert r["min_safety"]>0

def test_pb004b_no_hidden_reward_in_policy_logic():
    import inspect
    src=inspect.getsource(SafeExplorer)
    assert "hidden" not in src.lower()
    assert "WATER_HIDDEN" not in src

def test_pb004b_within_episode_limit():
    assert run_unknown_dynamics()["steps"] <= 100
