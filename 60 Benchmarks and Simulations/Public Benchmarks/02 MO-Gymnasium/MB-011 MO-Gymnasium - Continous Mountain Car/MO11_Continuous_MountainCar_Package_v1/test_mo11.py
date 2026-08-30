
import unittest, json
R=json.load(open("/mnt/data/mo11_mountaincarcontinuous/mo11_result.json"))
class T(unittest.TestCase):
    def test_candidates(self): self.assertEqual(R["candidate_magnitudes"],101)
    def test_full_success_nonzero(self): self.assertGreater(R["full_success_candidates"],0)
    def test_pareto_nonzero(self): self.assertGreater(R["pareto_candidates"],0)
    def test_supported_exist(self): self.assertGreater(R["supported_pareto_candidates"],0)
    def test_unsupported_exist(self): self.assertGreater(R["unsupported_pareto_candidates"],0)
    def test_counts_partition(self): self.assertEqual(R["pareto_candidates"],R["supported_pareto_candidates"]+R["unsupported_pareto_candidates"])
    def test_m040_unsupported(self): self.assertIn(0.4,R["unsupported_magnitudes"])
    def test_adequacy_unique(self): self.assertEqual(R["adequacy_probe"]["qualifying_magnitudes"],[0.4])
    def test_coast_fails(self): self.assertEqual(R["coast"]["successes"],0)
    def test_m020_succeeds(self): self.assertEqual(R["m020"]["successes"],5)
    def test_m100_succeeds(self): self.assertEqual(R["m100"]["successes"],5)
    def test_m020_fuel_better_than_m100(self): self.assertGreater(R["m020"]["mean_fuel_reward"],R["m100"]["mean_fuel_reward"])
    def test_m100_faster_than_m020(self): self.assertLess(R["m100"]["mean_steps"],R["m020"]["mean_steps"])
if __name__=="__main__": unittest.main()
