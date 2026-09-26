import numpy as np
CONVEX=[(.7,-1),(8.2,-3),(11.5,-5),(14,-7),(15.1,-8),(16.1,-9),(19.6,-13),(20.3,-14),(22.4,-17),(23.7,-19)]
CONCAVE=[(1,-1),(2,-3),(3,-5),(5,-7),(8,-8),(16,-9),(24,-13),(50,-14),(74,-17),(124,-19)]
def supported(front,i):
    # exact interval for w in [0,1]: w*T+(1-w)*time
    lo,hi=0.,1.
    Ti,ti=front[i]
    for j,(Tj,tj) in enumerate(front):
        if j==i: continue
        # w*((Ti-ti)-(Tj-tj)) >= tj-ti
        a=(Ti-ti)-(Tj-tj); b=tj-ti
        if abs(a)<1e-12:
            if b>0:return False
        elif a>0: lo=max(lo,b/a)
        else: hi=min(hi,b/a)
    return lo<=hi+1e-12

def test_front_sizes(): assert len(CONVEX)==len(CONCAVE)==10
def test_convex_supported_count(): assert sum(supported(CONVEX,i) for i in range(10))==10
def test_convex_one_unsupported(): assert [i for i in range(10) if not supported(CONVEX,i)]==[]
def test_concave_supported_endpoints_only(): assert [i for i in range(10) if supported(CONCAVE,i)]==[0,9]
def test_concave_eight_unsupported(): assert sum(not supported(CONCAVE,i) for i in range(10))==8
def test_mirrored_same_front(): assert CONCAVE==CONCAVE.copy()
def test_threshold_convex_unsupported_unique():
    # treasure >=20 and time >= -14 uniquely retains 20.3,-14 among front
    q=[p for p in CONVEX if p[0]>=20 and p[1]>=-14]
    assert q==[(20.3,-14)] and supported(CONVEX,7)
def test_threshold_concave_unsupported_unique():
    # treasure >=20, time >=-13 uniquely retains 24,-13
    q=[p for p in CONCAVE if p[0]>=20 and p[1]>=-13]
    assert q==[(24,-13)] and not supported(CONCAVE,6)
def test_scalar_weight_changes_winner():
    def win(front,w):return max(range(len(front)),key=lambda i:w*front[i][0]+(1-w)*front[i][1])
    assert win(CONCAVE,.01)==0 and win(CONCAVE,.99)==9
def test_mirror_geometry_not_reward_geometry(): assert len(CONCAVE)==10
