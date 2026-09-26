import unittest

FRONT = [(-1.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,1.0),(0.0,1.0,0.0),(0.0,1.0,1.0)]

def scalar(v,w):
    return sum(a*b for a,b in zip(v,w))

def adequate_both_safe(v):
    enemy,gold,gem=v
    return enemy==0 and gold>=1 and gem>=1

class ResourceGatheringCoverage(unittest.TestCase):
    def test_front_has_five_source_points(self): self.assertEqual(len(FRONT),5)
    def test_death_terminal_vector(self): self.assertIn((-1.0,0.0,0.0),FRONT)
    def test_both_resources_vector(self): self.assertIn((0.0,1.0,1.0),FRONT)
    def test_both_dominates_gold(self): self.assertGreater(scalar((0,1,1),(0,1,1)),scalar((0,1,0),(0,1,1)))
    def test_both_dominates_gem(self): self.assertGreater(scalar((0,1,1),(0,1,1)),scalar((0,0,1),(0,1,1)))
    def test_gold_priority_selectable(self): self.assertEqual((0.0,1.0,1.0),max(FRONT,key=lambda v:scalar(v,(1,3,1))))
    def test_gem_priority_selectable(self): self.assertEqual((0.0,1.0,1.0),max(FRONT,key=lambda v:scalar(v,(1,1,3))))
    def test_both_safe_unique_adequate(self): self.assertEqual([v for v in FRONT if adequate_both_safe(v)],[(0.0,1.0,1.0)])
    def test_death_inadequate(self): self.assertFalse(adequate_both_safe((-1,0,0)))
    def test_partial_returns_inadequate(self): self.assertFalse(adequate_both_safe((0,1,0)) or adequate_both_safe((0,0,1)))

if __name__=="__main__": unittest.main()
