
import unittest, json
R=json.load(open("/mnt/data/mo07_breakable_bottles/mo07_result.json"))
class TestMO07(unittest.TestCase):
    def test_no_drop_probability(self): self.assertAlmostEqual(R["p_no_drop"],.729,12)
    def test_drop_probability(self): self.assertAlmostEqual(R["p_any_drop"],.271,12)
    def test_cautious_steps(self): self.assertEqual(R["cautious_return"][0],-18)
    def test_cautious_no_potential_loss(self): self.assertEqual(R["cautious_return"][2],0)
    def test_batch_faster_expected(self): self.assertLess(R["expected_batch_steps"],18)
    def test_batch_has_irreversible_expected_penalty(self): self.assertLess(R["batch_expected_return"][2],0)
    def test_batch_expected_steps(self): self.assertAlmostEqual(R["expected_batch_steps"],12.439,9)
    def test_recoverable_faster_than_breakable_replacement(self): self.assertLess(R["expected_recoverable_steps"],R["expected_batch_steps"])
    def test_recoverable_potential_restored(self): self.assertEqual(R["recoverable_expected_return"][2],0)
    def test_scalar_threshold_positive(self): self.assertGreater(R["potential_weight_break_even"],20)
    def test_mc_batch(self): self.assertLess(abs(R["mc_batch_steps"]-R["expected_batch_steps"]),.05)
    def test_mc_drop(self): self.assertLess(abs(R["mc_batch_drop"]-R["p_any_drop"]),.005)
if __name__=="__main__": unittest.main()
