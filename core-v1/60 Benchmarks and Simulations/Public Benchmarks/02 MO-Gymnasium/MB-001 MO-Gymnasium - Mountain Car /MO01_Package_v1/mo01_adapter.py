import math
from dataclasses import dataclass, asdict

FORCE=0.001
GRAVITY=0.0025
MIN_POSITION=-1.2
MAX_POSITION=0.6
MAX_SPEED=0.07
GOAL_POSITION=0.5
MAX_STEPS=200

@dataclass
class Episode:
    start: float
    policy: str
    reached: bool
    steps: int
    reverse_actions: int
    forward_actions: int
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


def choose_action(name, state, t):
    p,v=state
    if name == 'momentum':
        return 2 if v >= 0 else 0
    if name == 'position_switch':
        # build leftward potential energy, then drive right
        return 0 if p > -0.75 and t < 60 else 2
    if name == 'always_right': return 2
    if name == 'always_left': return 0
    if name == 'coast': return 1
    if name == 'alternate': return 0 if t % 2 == 0 else 2
    raise ValueError(name)


def run(policy, start):
    state=(start,0.0)
    rev=fwd=0
    reached=False
    steps=0
    for t in range(MAX_STEPS):
        a=choose_action(policy,state,t)
        rev += (a==0); fwd += (a==2)
        state=step(state,a)
        steps=t+1
        if state[0] >= GOAL_POSITION:
            reached=True
            break
    vec=(-float(steps), -float(rev), -float(fwd))
    return Episode(start,policy,reached,steps,rev,fwd,vec,state[0],state[1])


def scalar(vec,w): return sum(a*b for a,b in zip(vec,w))

def main():
    starts=[-0.60,-0.55,-0.50,-0.45,-0.40]
    policies=['momentum','position_switch','always_right','always_left','coast','alternate']
    rows=[run(p,s) for s in starts for p in policies]
    for w in [(1.0,0,0),(1.0,0.05,0.05),(1.0,0.1,0.1),(1.0,0.5,0.5)]:
        print('weights',w)
        for s in starts:
            rs=[r for r in rows if r.start==s]
            winner=max(rs,key=lambda r: scalar(r.return_vector,w))
            print(s,winner.policy,winner.reached,winner.steps,winner.reverse_actions,winner.forward_actions,scalar(winner.return_vector,w))
    print('\nEpisodes')
    for r in rows: print(asdict(r))

if __name__=='__main__': main()
