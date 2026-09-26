
import unittest,json
R=json.load(open("/mnt/data/mo15_supermario/mo15_result.json"))
class T(unittest.TestCase):
 def test_reg(self): self.assertEqual(R["registration"],"mo-supermario-v0")
 def test_dim(self): self.assertEqual(len(R["reward_order"]),5)
 def test_actions(self): self.assertEqual(R["action_space"],"Discrete(256)")
 def test_death_penalty(self): self.assertEqual(R["reward_bounds"]["death"],[-25,0])
 def test_coin(self): self.assertEqual(R["reward_bounds"]["coin"],[0,100])
 def test_two_terminations(self): self.assertEqual(len(R["termination"]),2)
 def test_fatal_is_not_adequate(self): self.assertLess(R["controlled_policies"]["fatal_progress"][2],0)
 def test_safe_is_adequate(self): self.assertEqual(R["controlled_policies"]["safe_progress"][2],0)
 def test_scalar_can_select_fatal(self): self.assertIn("fatal",R["scalar_winner"])
 def test_adequacy_excludes_fatal(self): self.assertNotIn("fatal",R["adequacy_winner"])
 def test_coin_distinct(self): self.assertEqual(R["controlled_policies"]["coin_detour"][3],100)
 def test_enemy_distinct(self): self.assertGreater(R["controlled_policies"]["enemy_detour"][4],0)
if __name__=="__main__": unittest.main()
