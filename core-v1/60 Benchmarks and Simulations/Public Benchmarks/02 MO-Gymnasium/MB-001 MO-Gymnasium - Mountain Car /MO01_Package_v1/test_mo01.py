import unittest
from mo01_adapter import run, scalar, step, GOAL_POSITION

STARTS=[-0.60,-0.55,-0.50,-0.45,-0.40]
POLICIES=['momentum','position_switch','always_right','always_left','coast','alternate']

def winner(start,w, adequate_only=False):
    rows=[run(p,start) for p in POLICIES]
    if adequate_only:
        rows=[r for r in rows if r.reached]
    return max(rows,key=lambda r:scalar(r.return_vector,w))

class MO01Tests(unittest.TestCase):
    def test_documented_transition_equation(self):
        p,v=step((-0.5,0.0),2)
        self.assertAlmostEqual(v,0.001-0.0025*__import__('math').cos(-1.5),12)
        self.assertAlmostEqual(p,-0.5+v,12)
    def test_reward_vector_shape_and_time(self):
        r=run('momentum',-0.5)
        self.assertEqual(len(r.return_vector),3)
        self.assertEqual(r.return_vector[0],-r.steps)
    def test_action_penalties_count(self):
        r=run('momentum',-0.5)
        self.assertEqual(r.return_vector[1],-r.reverse_actions)
        self.assertEqual(r.return_vector[2],-r.forward_actions)
    def test_momentum_reaches_all_frozen_starts(self):
        self.assertTrue(all(run('momentum',s).reached for s in STARTS))
    def test_other_simple_policies_fail_all_frozen_starts(self):
        for p in ['always_right','always_left','coast','alternate','position_switch']:
            self.assertTrue(all(not run(p,s).reached for s in STARTS),p)
    def test_time_only_scalar_selects_momentum(self):
        self.assertTrue(all(winner(s,(1,0,0)).policy=='momentum' for s in STARTS))
    def test_moderate_linear_scalar_selects_momentum(self):
        self.assertTrue(all(winner(s,(1,.5,.5)).policy=='momentum' for s in STARTS))
    def test_high_move_penalty_scalar_selects_coast(self):
        self.assertTrue(all(winner(s,(1,1,1)).policy=='coast' for s in STARTS))
    def test_adequacy_gate_rejects_timeout(self):
        self.assertTrue(all(winner(s,(1,1,1),adequate_only=True).policy=='momentum' for s in STARTS))
    def test_goal_position(self):
        self.assertEqual(GOAL_POSITION,0.5)
    def test_bounded_containment_threshold_positive(self):
        # symmetric movement weight alpha: momentum score = -(1+alpha)*steps, coast=-200
        thresholds=[200/run('momentum',s).steps-1 for s in STARTS]
        self.assertGreater(min(thresholds),0.6)
        self.assertLess(min(thresholds),0.62)

if __name__=='__main__': unittest.main()
