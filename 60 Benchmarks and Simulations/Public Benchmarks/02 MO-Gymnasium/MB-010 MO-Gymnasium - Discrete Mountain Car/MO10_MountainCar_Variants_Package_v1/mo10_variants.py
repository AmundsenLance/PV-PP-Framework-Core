import math, json
from dataclasses import dataclass, asdict

FORCE=0.001
GRAVITY=0.0025
MIN_POSITION=-1.2
MAX_POSITION=0.6
MAX_SPEED=0.07
GOAL_POSITION=0.5
MAX_STEPS=200

STARTS=[-0.60,-0.55,-0.50,-0.45,-0.40]
POLICIES=['momentum','position_switch','always_right','always_left','coast','alternate']

VARIANTS={
    'mo-mountaincar-3d-v0': ('time','move','speed'),
    'mo-mountaincar-timemove-v0': ('time','move'),
    'mo-mountaincar-timespeed-v0': ('time','speed'),
}

@dataclass
class Episode:
    env: str
    start: float
    policy: str
    reached: bool
    steps: int
    move_actions: int
    speed_sum: float
    return_vector: tuple
    final_position: float
    final_velocity: float

def step(state, action):
    position, velocity = state
    velocity += (action - 1) * FORCE - math.cos(3 * position) * GRAVITY
    velocity = max(-MAX_SPEED, min(MAX_SPEED, velocity))
    position += velocity
    position = max(MIN_POSITION, min(MAX_POSITION, position))
    if position == MIN_POSITION and velocity < 0:
        velocity = 0.0
    return position, velocity

def choose_action(name,state,t):
    p,v=state
    if name=='momentum': return 2 if v >= 0 else 0
    if name=='position_switch': return 0 if p > -0.75 and t < 60 else 2
    if name=='always_right': return 2
    if name=='always_left': return 0
    if name=='coast': return 1
    if name=='alternate': return 0 if t%2==0 else 2
    raise ValueError(name)

def run(env,policy,start):
    fields=VARIANTS[env]
    state=(start,0.0); moves=0; speed_sum=0.; reached=False
    for t in range(MAX_STEPS):
        a=choose_action(policy,state,t)
        moves += int(a != 1)
        state=step(state,a)
        speed_sum += 15.0 * abs(state[1])
        steps=t+1
        if state[0] >= GOAL_POSITION:
            reached=True; break
    vals={'time':-float(steps-1 if reached else steps),'move':-float(moves),'speed':float(speed_sum)}
    return Episode(env,start,policy,reached,steps,moves,speed_sum,tuple(vals[k] for k in fields),state[0],state[1])

def scalar(v,w): return sum(a*b for a,b in zip(v,w))

def winner(env,start,w,adequate=False):
    rows=[run(env,p,start) for p in POLICIES]
    if adequate: rows=[r for r in rows if r.reached]
    return max(rows,key=lambda r:scalar(r.return_vector,w))

def threshold_timemove(start):
    # alpha on move penalty in score time + alpha*move. momentum vs coast.
    m=run('mo-mountaincar-timemove-v0','momentum',start)
    # coast score -200, momentum = -steps-alpha*steps (all momentum actions move)
    # coast time return is -200; momentum time return is -(steps-1), move=-steps
    return (MAX_STEPS-(m.steps-1))/m.steps

def threshold_timespeed(start):
    m=run('mo-mountaincar-timespeed-v0','momentum',start)
    c=run('mo-mountaincar-timespeed-v0','coast',start)
    # -m.steps + beta*m.speed >= -c.steps + beta*c.speed
    mt=-(m.steps-1); ct=-c.steps
    return (ct-mt)/(m.speed_sum-c.speed_sum)

def main():
    out={'starts':STARTS,'variants':{}}
    for env in VARIANTS:
        rows=[run(env,p,s) for s in STARTS for p in POLICIES]
        dim=len(VARIANTS[env])
        eq=(1.0,)*dim
        out['variants'][env]={
          'fields':VARIANTS[env],
          'equal_weight_winners':{str(s):asdict(winner(env,s,eq)) for s in STARTS},
          'equal_weight_adequate_winners':{str(s):asdict(winner(env,s,eq,True)) for s in STARTS},
          'momentum':{str(s):asdict(run(env,'momentum',s)) for s in STARTS},
          'coast':{str(s):asdict(run(env,'coast',s)) for s in STARTS},
        }
    out['timemove_alpha_thresholds']={str(s):threshold_timemove(s) for s in STARTS}
    out['timespeed_beta_thresholds']={str(s):threshold_timespeed(s) for s in STARTS}
    open('/mnt/data/mo10_mountain_variants/mo10_result.json','w').write(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
