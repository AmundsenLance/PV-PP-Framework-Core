import numpy as np
from mo03_adapter import *

def test_constants():
    assert W_IRR==50 and Q_FLO_D==30 and H_FLO_U==50 and DAM_INFLOW_MEAN==40

def test_action_bounds_low_state():
    assert action_bounds(20)==(0.0,20)

def test_action_bounds_high_state():
    assert action_bounds(140)==(40,140)

def test_joint_water_downstream_zero_impossible():
    # r1=0 requires a>=50 while r3=0 requires a<=30
    assert W_IRR > Q_FLO_D

def test_all_four_zero_empty_all_frozen_states():
    for s in [20.,40.,60.,100.,140.]:
        assert zero_adequate_actions(s,[0,1,2,3])==[]

def test_safety_feasible_state20():
    xs=zero_adequate_actions(20,[0,3])
    assert xs[0][0]==10 and xs[-1][0]==20

def test_safety_unique_state40():
    xs=zero_adequate_actions(40,[0,3])
    assert len(xs)==1 and xs[0][0]==30

def test_safety_empty_above_boundary():
    for s in [60.,100.,140.]: assert zero_adequate_actions(s,[0,3])==[]

def test_equal_scalar_still_returns_action_when_all4_infeasible():
    for s in [20.,40.,60.,100.,140.]:
        assert scalar_best(s,np.ones(4)) is not None
        assert zero_adequate_actions(s,[0,1,2,3])==[]

def test_equal_scalar_actions_expected():
    expected={20.:20.,40.:40.,60.:50.,100.:50.,140.:50.}
    for s,a in expected.items(): assert scalar_best(s,np.ones(4))[1]==a

def test_water_vs_downstream_conflict_visible_at_scalar_winner():
    _,a,_,r=scalar_best(60,np.ones(4))
    assert a==50 and r[1]==0 and r[3]==-20
