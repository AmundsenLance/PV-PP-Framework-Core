
from pb009h_adapter import *

def test_fixed_a_defeated():
    assert run_deterministic(fixed_a, 1000) == 0.0

def test_fixed_b_defeated():
    assert run_deterministic(fixed_b, 1000) == 0.0

def test_alternation_defeated():
    assert run_deterministic(alternate, 1000) == 0.0

def test_repeating_pattern_defeated():
    assert run_deterministic(aab, 1000) == 0.0

def test_adaptive_deterministic_rule_defeated():
    assert run_deterministic(last_outcome_switch, 1000) == 0.0

def test_exact_mixed_symmetry():
    assert exact_mixed_success(.25) == .25
    assert exact_mixed_success(.75) == .25

def test_half_half_is_maximin():
    ps=[i/100 for i in range(101)]
    best=max(ps,key=exact_mixed_success)
    assert best == .5
    assert exact_mixed_success(best) == .5

def test_half_half_simulation_near_half():
    x=run_mixed(.5,50000,1)
    assert .49 < x < .51

def test_biased_mix_is_worse_than_half():
    assert exact_mixed_success(.4) < exact_mixed_success(.5)
    assert exact_mixed_success(.6) < exact_mixed_success(.5)

def test_pure_mixes_equivalent_to_deterministic():
    assert exact_mixed_success(0.0) == 0.0
    assert exact_mixed_success(1.0) == 0.0

def test_foe_cannot_condition_on_private_draw():
    assert PerfectPredictorFoe.reward_box_for_mixed(.5) in (0,1)
