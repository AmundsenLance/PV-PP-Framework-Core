import unittest, json, sys
sys.path.insert(0,'/mnt/data/mo10_mountain_variants')
from mo10_variants import *
class TestMO10(unittest.TestCase):
    def test_three_registered_variants(self): self.assertEqual(len(VARIANTS),3)
    def test_3d_shape(self): self.assertEqual(len(run('mo-mountaincar-3d-v0','momentum',-.5).return_vector),3)
    def test_timemove_shape(self): self.assertEqual(len(run('mo-mountaincar-timemove-v0','momentum',-.5).return_vector),2)
    def test_timespeed_shape(self): self.assertEqual(len(run('mo-mountaincar-timespeed-v0','momentum',-.5).return_vector),2)
    def test_momentum_reaches_all(self):
        for env in VARIANTS: self.assertTrue(all(run(env,'momentum',s).reached for s in STARTS))
    def test_coast_fails_all(self):
        for env in VARIANTS: self.assertTrue(all(not run(env,'coast',s).reached for s in STARTS))
    def test_speed_nonnegative(self): self.assertGreater(run('mo-mountaincar-timespeed-v0','momentum',-.5).speed_sum,0)
    def test_timemove_equal_weights_prefers_coast(self):
        self.assertTrue(all(winner('mo-mountaincar-timemove-v0',s,(1,1)).policy=='coast' for s in STARTS))
    def test_3d_equal_weights_is_start_sensitive(self):
        wins=[winner('mo-mountaincar-3d-v0',s,(1,1,1)).policy for s in STARTS]
        self.assertEqual(wins[:2],['momentum','momentum'])
        self.assertEqual(wins[2:],['coast','coast','coast'])
    def test_timespeed_equal_weights_prefers_momentum(self):
        self.assertTrue(all(winner('mo-mountaincar-timespeed-v0',s,(1,1)).policy=='momentum' for s in STARTS))
    def test_adequacy_restores_momentum(self):
        for env in VARIANTS:
            w=(1,)*len(VARIANTS[env])
            self.assertTrue(all(winner(env,s,w,True).policy=='momentum' for s in STARTS))
    def test_timemove_threshold_matches_base_family(self):
        vals=[threshold_timemove(s) for s in STARTS]
        self.assertGreater(min(vals),.62); self.assertLess(min(vals),.63)
    def test_timespeed_beta_threshold_negative(self):
        # Positive speed weight only strengthens momentum against coast in the frozen policy set.
        self.assertTrue(all(threshold_timespeed(s)<0 for s in STARTS))
if __name__=='__main__': unittest.main()
