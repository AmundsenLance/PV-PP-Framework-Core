import unittest, importlib.util
spec=importlib.util.spec_from_file_location('fw','/mnt/data/mo06_fishwood/fishwood_analysis.py')
fw=importlib.util.module_from_spec(spec); spec.loader.exec_module(fw)
class TestFishwood(unittest.TestCase):
    def test_horizon(self): self.assertEqual(fw.H,200)
    def test_defaults(self): self.assertEqual((fw.P_FISH,fw.P_WOOD),(0.1,0.9))
    def test_expected_all_wood(self): self.assertEqual(fw.expected_from_state_counts(0),(0.0,180.0))
    def test_expected_all_fish_states(self): self.assertEqual(fw.expected_from_state_counts(200),(20.0,0.0))
    def test_balanced_expected(self): self.assertEqual(fw.expected_from_state_counts(100),(10.0,90.0))
    def test_equal_weights_choose_wood(self):
        vals=[fw.linear(v,(1,1)) for v in fw.points]
        self.assertEqual(vals.index(max(vals)),0)
    def test_tie_weights_support_all_allocations(self):
        vals=[fw.linear(v,(9,1)) for v in fw.points]
        self.assertTrue(max(vals)-min(vals)<1e-9)
    def test_fish_heavy_weights_choose_fish(self):
        vals=[fw.linear(v,(10,1)) for v in fw.points]
        self.assertEqual(vals.index(max(vals)),200)
    def test_joint_threshold_unique_allocation(self): self.assertEqual(fw.adequate,[100])
    def test_normalized_min_utility_unique_allocation(self): self.assertEqual(fw.uwinners,[100])
    def test_mc_wood_close(self): self.assertAlmostEqual(fw.mc['wood']['mean_wood'],180,delta=1.0)
    def test_mc_alternate_close(self):
        self.assertAlmostEqual(fw.mc['alternate']['mean_fish'],10,delta=.5)
        self.assertAlmostEqual(fw.mc['alternate']['mean_wood'],90,delta=1.0)
if __name__=='__main__': unittest.main()
