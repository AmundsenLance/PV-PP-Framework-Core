import random, json
H=200
P_FISH=0.1
P_WOOD=0.9

def expected_from_state_counts(fish_steps:int):
    wood_steps=H-fish_steps
    return (P_FISH*fish_steps, P_WOOD*wood_steps)  # code ordering: fish, wood

def linear(v,w): return v[0]*w[0]+v[1]*w[1]

def adequacy(v): return v[0] >= 10.0-1e-12 and v[1] >= 90.0-1e-12

def normalized_min_utility(v): return min(v[0]/10.0, v[1]/90.0)

points=[expected_from_state_counts(f) for f in range(H+1)]
weights=[(1.0,1.0),(9.0,1.0),(10.0,1.0),(1.0,1.0)]
probes={}
for w in [(1,1),(9,1),(10,1),(1,9)]:
    vals=[linear(v,w) for v in points]
    m=max(vals)
    winners=[f for f,x in enumerate(vals) if abs(x-m)<1e-9]
    probes[str(w)]={"max":m,"winner_fish_steps":winners[:10],"winner_count":len(winners)}
adequate=[f for f,v in enumerate(points) if adequacy(v)]
uvals=[normalized_min_utility(v) for v in points]
umax=max(uvals); uwinners=[f for f,u in enumerate(uvals) if abs(u-umax)<1e-12]

# Source-step Monte Carlo for three fixed action patterns. Reward is collected from CURRENT state, then action sets next state.
def run_policy(policy, seed):
    rng=random.Random(seed)
    state=1 # 1=wood, 0=fish, source starts in woods
    fish=wood=0
    for t in range(H):
        if state==1:
            if rng.random()<P_WOOD: wood+=1
        else:
            if rng.random()<P_FISH: fish+=1
        action=policy(t,state)
        state=action
    return fish,wood
policies={
    "wood": lambda t,s:1,
    "fish": lambda t,s:0,
    "alternate": lambda t,s:0 if (t%2==0) else 1,
}
mc={}
for name,pol in policies.items():
    vals=[run_policy(pol,seed) for seed in range(2000)]
    mc[name]={"mean_fish":sum(v[0] for v in vals)/len(vals),"mean_wood":sum(v[1] for v in vals)/len(vals)}

out={
 "horizon":H,"p_fish":P_FISH,"p_wood":P_WOOD,
 "expected_endpoints":{"all_wood":points[0],"all_fish_state":points[200],"balanced_100_100":points[100]},
 "linear_probes":probes,
 "adequate_fish_steps":adequate,
 "nonlinear_utility_winners":uwinners,
 "mc":mc,
 "documentation_note":"Summary table and executable code use reward ordering [fish, wood]; detailed reward bullets on Fishwood page reverse the labels. Analysis follows executable source code and summary table."
}
print(json.dumps(out,indent=2))
open('/mnt/data/mo06_fishwood/mo06_result.json','w').write(json.dumps(out,indent=2))
