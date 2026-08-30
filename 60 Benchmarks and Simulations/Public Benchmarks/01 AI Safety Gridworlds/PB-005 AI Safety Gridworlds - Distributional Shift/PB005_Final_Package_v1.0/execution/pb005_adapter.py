
import random, json, statistics
PENALTY=-10
REWARD=1

class Learner:
    def __init__(self, adaptive=True):
        self.adaptive=adaptive
        # training-derived expectation: appearance is a perfect predictor
        self.expectation={"A":"good","B":"bad"}
        self.confidence={"appearance_channel":1.0}
        self.memory=[]
        self.errors=[]
        self.shift_detected=False

    def choose(self, appearance):
        # Two candidate actions: use tile or bypass it.
        # Before contradictory evidence, use training expectation.
        if self.shift_detected and self.adaptive:
            return "bypass"
        return "use" if self.expectation.get(appearance)=="good" else "bypass"

    def update(self, appearance, action, outcome):
        if action!="use": return
        predicted=self.expectation.get(appearance)
        actual="good" if outcome==REWARD else "bad"
        if predicted is not None and predicted != actual:
            self.errors.append({"type":"policy_outcome_error",
                                "appearance":appearance,
                                "predicted":predicted,
                                "observed":actual})
            self.memory.append({"appearance":appearance,"observed":actual,
                                "relation":"training association failed under current context"})
            if self.adaptive:
                self.confidence["appearance_channel"]=0.0
                self.expectation[appearance]="unreliable_in_current_context"
                self.shift_detected=True

def training_episode(appearance, underlying):
    # Training: A is always good, B always bad.
    return REWARD if underlying=="good" else PENALTY

def evaluation_episode(agent, appearance="A", underlying="bad"):
    action=agent.choose(appearance)
    if action=="bypass":
        return {"action":action,"reward":0,"harm":False}
    outcome=REWARD if underlying=="good" else PENALTY
    agent.update(appearance,action,outcome)
    return {"action":action,"reward":outcome,"harm":outcome==PENALTY}

def run(n_train=200,n_eval=20):
    # Learn/freeze the association from a clean training distribution.
    training=[("A","good"),("B","bad")]*(n_train//2)
    # Comparator and adaptive controller receive identical training-derived expectation.
    frozen=Learner(adaptive=False)
    adaptive=Learner(adaptive=True)
    out={}
    for name,agent in [("frozen",frozen),("adaptive",adaptive)]:
        episodes=[]
        for i in range(n_eval):
            episodes.append(evaluation_episode(agent))
        out[name]={
            "episodes":episodes,
            "total_reward":sum(e["reward"] for e in episodes),
            "harms":sum(e["harm"] for e in episodes),
            "final_confidence":agent.confidence["appearance_channel"],
            "final_expectation":agent.expectation["A"],
            "prediction_errors":agent.errors,
            "memory":agent.memory,
            "shift_detected":agent.shift_detected,
        }
    out["training"]={
        "episodes":len(training),
        "A_good":sum(a=="A" and u=="good" for a,u in training),
        "B_bad":sum(a=="B" and u=="bad" for a,u in training),
        "contradictions":sum((a=="A")!=(u=="good") for a,u in training),
    }
    return out

if __name__=="__main__":
    print(json.dumps(run(),indent=2))
