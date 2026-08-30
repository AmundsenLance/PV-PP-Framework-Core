
import unittest, json
R=json.load(open("/mnt/data/mo12_lunar_lander/mo12_result.json"))
class T(unittest.TestCase):
    def test_two_regs(self): self.assertEqual(len(R["registrations"]),2)
    def test_current_v3_discrete(self): self.assertIn("mo-lunar-lander-v3",R["registrations"])
    def test_current_v3_continuous(self): self.assertIn("mo-lunar-lander-continuous-v3",R["registrations"])
    def test_reward_dim(self): self.assertEqual(len(R["reward_order"]),4)
    def test_nonterminal_main_scalar(self): self.assertAlmostEqual(R["probes"]["nonterminal_main"]["original"],4.7)
    def test_nonterminal_main_linear_matches(self): self.assertAlmostEqual(R["probes"]["nonterminal_main"]["original"],R["probes"]["nonterminal_main"]["linear_1_1_.3_.03"])
    def test_nonterminal_side_matches(self): self.assertAlmostEqual(R["probes"]["nonterminal_side"]["original"],R["probes"]["nonterminal_side"]["linear_1_1_.3_.03"])
    def test_terminal_land_overwrite(self): self.assertEqual(R["probes"]["terminal_land"]["original"],100.0)
    def test_terminal_land_linear_not_exact(self): self.assertNotAlmostEqual(R["probes"]["terminal_land"]["original"],R["probes"]["terminal_land"]["linear_1_1_.3_.03"])
    def test_terminal_crash_overwrite(self): self.assertEqual(R["probes"]["terminal_crash"]["original"],-100.0)
    def test_terminal_crash_linear_not_exact(self): self.assertNotAlmostEqual(R["probes"]["terminal_crash"]["original"],R["probes"]["terminal_crash"]["linear_1_1_.3_.03"])
    def test_no_global_fixed_linear_recovery(self): self.assertFalse(R["global_fixed_linear_recovery_of_original_reward"])
    def test_shaping_unbounded(self): self.assertEqual(R["reward_bounds"]["shaping"],["-inf","inf"])
if __name__=="__main__": unittest.main()
