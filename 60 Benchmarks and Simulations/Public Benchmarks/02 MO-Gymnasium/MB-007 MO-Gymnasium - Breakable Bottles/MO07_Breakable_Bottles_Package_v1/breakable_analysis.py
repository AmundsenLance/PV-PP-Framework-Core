
import random, json

P_DROP=.1
N=200000

def batch(seed=1):
    rng=random.Random(seed)
    steps=[]
    drops=0
    for _ in range(N):
        # 4 left + 2 pickups + outbound right trip
        dropped=False
        s=10
        for loc in (1,2,3):
            if rng.random()<P_DROP:
                dropped=True
                drops += 1
                break
        if dropped:
            s += 9  # return to source, pick one, redeliver
        steps.append(s)
    return sum(steps)/N, drops/N

def recoverable(seed=2):
    rng=random.Random(seed)
    steps=[]
    drops=0
    for _ in range(N):
        s=10
        drop_loc=None
        for loc in (1,2,3):
            if rng.random()<P_DROP:
                drop_loc=loc
                drops+=1
                break
        if drop_loc is not None:
            s += 2*(4-drop_loc)+1
        steps.append(s)
    return sum(steps)/N, drops/N

p_no=.9**3
p_drop=1-p_no
expected_batch=10*p_no+19*p_drop
expected_recover=10*p_no + .1*17 + .09*15 + .081*13
threshold=(18-expected_batch)/p_drop

mc_batch=batch()
mc_recover=recoverable()
result={
 "p_no_drop":p_no, "p_any_drop":p_drop,
 "cautious_return":[-18,50,0],
 "batch_expected_return":[-expected_batch,50,-p_drop],
 "recoverable_expected_return":[-expected_recover,50,0],
 "expected_batch_steps":expected_batch,
 "expected_recoverable_steps":expected_recover,
 "potential_weight_break_even":threshold,
 "mc_batch_steps":mc_batch[0], "mc_batch_drop":mc_batch[1],
 "mc_recover_steps":mc_recover[0], "mc_recover_drop":mc_recover[1]
}
print(json.dumps(result,indent=2))
open("/mnt/data/mo07_breakable_bottles/mo07_result.json","w").write(json.dumps(result,indent=2))
