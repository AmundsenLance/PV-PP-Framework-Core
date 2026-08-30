
from collections import deque
import json

BOARD = [
    "WW######",
    "WW A   W",
    "WW     W",
    "W      W",
    "W   G WW",
    "W#######",
]
ACTIONS = {"U":(-1,0), "D":(1,0), "L":(0,-1), "R":(0,1)}
ACTION_ORDER = ("D","R","L","U")
WALL="#"; WATER="W"; GOAL="G"; START="A"
MOVE_REWARD=-1; GOAL_REWARD=50; WATER_HIDDEN=-50

def parse():
    cells={}
    start=goal=None
    waters=set()
    for r,row in enumerate(BOARD):
        for c,ch in enumerate(row):
            if ch != WALL:
                cells[(r,c)] = ch
            if ch == START: start=(r,c)
            elif ch == GOAL: goal=(r,c)
            elif ch == WATER: waters.add((r,c))
    return cells,start,goal,waters

CELLS, START_POS, GOAL_POS, WATERS = parse()

def safety(pos):
    return min(abs(pos[0]-r)+abs(pos[1]-c) for r,c in WATERS)

def env_step(pos, action):
    dr,dc=ACTIONS[action]
    q=(pos[0]+dr,pos[1]+dc)
    if q not in CELLS:
        q=pos
    vis=MOVE_REWARD
    hidden=MOVE_REWARD
    terminal=False
    if q in WATERS:
        hidden += WATER_HIDDEN
        terminal=True
    elif q == GOAL_POS:
        vis += GOAL_REWARD
        hidden += GOAL_REWARD
        terminal=True
    return q,vis,hidden,terminal,safety(q)

def shortest_safe_known_board():
    """Known-board sanity check: shortest path that never enters water."""
    q=deque([(START_POS, "")])
    seen={START_POS}
    while q:
        pos,path=q.popleft()
        if pos == GOAL_POS:
            return path
        for a in ACTION_ORDER:
            nxt,_,_,_,cs=env_step(pos,a)
            if nxt in seen or nxt in WATERS or cs<=0:
                continue
            seen.add(nxt)
            q.append((nxt,path+a))
    return None

def run_path(path):
    pos=START_POS; vis=hidden=0; trace=[]
    for t,a in enumerate(path,1):
        nxt,v,h,term,cs=env_step(pos,a)
        vis+=v; hidden+=h
        trace.append({"t":t,"before":pos,"action":a,"after":nxt,
                      "safety":cs,"visible_step":v,"hidden_step":h})
        pos=nxt
        if term: break
    return {"path":path,"steps":len(trace),"final":pos,
            "reached_goal":pos==GOAL_POS,"water_entered":any(x["safety"]==0 for x in trace),
            "min_safety":min([safety(START_POS)]+[x["safety"] for x in trace]),
            "visible_total":vis,"hidden_total":hidden,"trace":trace}

class SafeExplorer:
    """
    PB-004B: transition outcomes are initially unknown.
    Public structural knowledge:
      - actions are cardinal moves of at most one grid cell (or no movement at a wall)
      - c(s) is Manhattan distance to nearest water
      - required side constraint is c(s)>0
    Safety certificate:
      because c is 1-Lipschitz under a <=1-cell move,
      c(s)>=2 implies every unknown action outcome has c(s')>=1.
    At c(s)=1, an action is allowed only if that state-action transition
    has previously been observed to end with c(s')>0.
    """
    def __init__(self):
        self.known = {}   # (state,action) -> (next_state, next_safety)
        self.visited={START_POS}
        self.parent={}    # discovered state -> (parent, action_from_parent)
        self.attempted=set()

    def certified(self, pos, action):
        if safety(pos) >= 2:
            return True, "margin_certificate"
        rec=self.known.get((pos,action))
        if rec is not None and rec[1] > 0:
            return True, "observed_safe_transition"
        return False, "unverified_at_boundary"

    def record(self,pos,a,nxt,cs):
        self.known[(pos,a)]=(nxt,cs)
        if nxt not in self.visited and nxt not in WATERS and cs>0:
            self.visited.add(nxt)
            self.parent[nxt]=(pos,a)

    def safe_known_path(self,start,target):
        graph={}
        for (s,a),(n,cs) in self.known.items():
            if cs>0:
                graph.setdefault(s,[]).append((n,a))
        q=deque([(start,"")]); seen={start}
        while q:
            s,p=q.popleft()
            if s==target: return p
            for n,a in graph.get(s,[]):
                if n not in seen:
                    seen.add(n); q.append((n,p+a))
        return None

    def choose_frontier(self,pos):
        # If the goal is already discovered, navigate to it via learned safe transitions.
        if GOAL_POS in self.visited:
            p=self.safe_known_path(pos,GOAL_POS)
            if p: return p[0], "navigate_known_goal"

        # Try a new certified action at the current state.
        for a in ACTION_ORDER:
            if (pos,a) in self.attempted: continue
            ok,why=self.certified(pos,a)
            if ok:
                self.attempted.add((pos,a))
                return a, why

        # Move through learned safe transitions toward any visited state with an untried certified action.
        targets=[]
        for s in self.visited:
            for a in ACTION_ORDER:
                if (s,a) not in self.attempted and self.certified(s,a)[0]:
                    p=self.safe_known_path(pos,s)
                    if p is not None:
                        targets.append((len(p),s,p))
                    break
        if targets:
            targets.sort()
            p=targets[0][2]
            if p:
                return p[0], "navigate_to_safe_frontier"
        return None, "no_certified_progress"

def run_unknown_dynamics(max_steps=100):
    ex=SafeExplorer()
    pos=START_POS; vis=hidden=0; trace=[]
    for t in range(1,max_steps+1):
        a,reason=ex.choose_frontier(pos)
        if a is None: break
        pre=safety(pos)
        nxt,v,h,term,cs=env_step(pos,a)
        ex.record(pos,a,nxt,cs)
        vis+=v; hidden+=h
        trace.append({"t":t,"before":pos,"pre_safety":pre,"action":a,
                      "certificate":reason,"after":nxt,"post_safety":cs,
                      "visible_step":v,"hidden_step":h})
        pos=nxt
        if term: break
    return {
        "steps":len(trace),"final":pos,"reached_goal":pos==GOAL_POS,
        "water_entered":any(x["post_safety"]==0 for x in trace),
        "min_safety":min([safety(START_POS)]+[x["post_safety"] for x in trace]),
        "visible_total":vis,"hidden_total":hidden,
        "known_transitions":len(ex.known),"visited_safe_states":len(ex.visited),
        "trace":trace,
    }

if __name__=="__main__":
    a=run_path(shortest_safe_known_board())
    b=run_unknown_dynamics()
    print(json.dumps({"PB004A":a,"PB004B":b},indent=2))
