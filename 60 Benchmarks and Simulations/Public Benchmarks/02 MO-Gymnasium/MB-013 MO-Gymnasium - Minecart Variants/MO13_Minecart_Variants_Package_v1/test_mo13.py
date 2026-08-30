
import unittest, json
R=json.load(open("/mnt/data/mo13_minecart_variants/mo13_result.json"))
class T(unittest.TestCase):
    def test_three_registrations(self): self.assertEqual(len(R["current_registrations"]),3)
    def test_baseline_already_covered(self): self.assertIn("MO-02",R["current_registrations"]["minecart-v0"]["status"])
    def test_rgb_equivalence(self): self.assertTrue(R["rgb_equivalence"]["same_entry_point"])
    def test_rgb_same_config(self): self.assertTrue(R["rgb_equivalence"]["same_config_as_baseline"])
    def test_rgb_reward_unchanged(self): self.assertFalse(R["rgb_equivalence"]["reward_semantics_changed"])
    def test_rgb_transition_unchanged(self): self.assertFalse(R["rgb_equivalence"]["transition_semantics_changed"])
    def test_det_candidates(self): self.assertEqual(R["deterministic_counts"]["candidate_return_vectors"],154)
    def test_det_pareto(self): self.assertEqual(R["deterministic_counts"]["pareto_unique"],10)
    def test_det_supported(self): self.assertEqual(R["deterministic_counts"]["linearly_supported"],6)
    def test_det_unsupported(self): self.assertEqual(R["deterministic_counts"]["linearly_unsupported"],4)
    def test_baseline_pattern_same(self): self.assertEqual(R["baseline_counts"]["linearly_unsupported"],4)
    def test_det_has_balanced_supported(self):
        pts=R["deterministic_pareto_points"]
        self.assertTrue(any(p["reward"][:2]==[0.75,0.75] and p["exact_supported"] for p in pts))
if __name__=="__main__": unittest.main()
