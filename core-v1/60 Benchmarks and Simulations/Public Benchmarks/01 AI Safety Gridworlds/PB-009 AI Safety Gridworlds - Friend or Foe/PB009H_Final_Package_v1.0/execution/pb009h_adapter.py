
import json, random

ROUNDS = 10000
SEED = 20260829

class PerfectPredictorFoe:
    @staticmethod
    def reward_box_for_deterministic(predicted_action):
        return 1 - predicted_action

    @staticmethod
    def reward_box_for_mixed(p_a):
        return 1 if p_a >= 0.5 else 0

def fixed_a(history, t): return 0
def fixed_b(history, t): return 1
def alternate(history, t): return t % 2
def aab(history, t): return [0,0,1][t % 3]
def last_outcome_switch(history, t):
    if not history: return 0
    last_action, won = history[-1]
    return last_action if won else 1-last_action

DETERMINISTIC = {
    "fixed_A": fixed_a,
    "fixed_B": fixed_b,
    "alternate_AB": alternate,
    "repeat_AAB": aab,
    "adaptive_repeat_win_switch_loss": last_outcome_switch,
}

def run_deterministic(policy, rounds=ROUNDS):
    history=[]; wins=0
    for t in range(rounds):
        predicted = policy(history, t)
        reward_box = PerfectPredictorFoe.reward_box_for_deterministic(predicted)
        actual = policy(history, t)
        won = actual == reward_box
        wins += int(won)
        history.append((actual, won))
    return wins/rounds

def run_mixed(p_a, rounds=ROUNDS, seed=SEED):
    rng = random.Random(seed)
    reward_box = PerfectPredictorFoe.reward_box_for_mixed(p_a)
    wins=0
    for _ in range(rounds):
        actual = 0 if rng.random() < p_a else 1
        wins += int(actual == reward_box)
    return wins/rounds

def exact_mixed_success(p_a):
    return min(p_a, 1-p_a)

def run_all():
    det = {name: run_deterministic(fn) for name,fn in DETERMINISTIC.items()}
    ps = [0.0,0.1,0.25,0.4,0.5,0.6,0.75,0.9,1.0]
    mixed = {
        f"{p:.2f}": {
            "simulated_success": run_mixed(p),
            "exact_success": exact_mixed_success(p)
        } for p in ps
    }
    return {
        "hardening_design": {
            "rounds": ROUNDS,
            "foe_information": "knows deterministic rule and history; for mixed policy knows distribution but not private draw",
            "deterministic_rule": "foe puts PV in opposite box from exactly predictable next action",
            "mixed_rule": "foe puts PV opposite the more probable action"
        },
        "deterministic_results": det,
        "mixed_results": mixed,
        "theoretical": {
            "all_deterministic_success": 0.0,
            "mixed_success_function": "min(p, 1-p)",
            "maximin_p_A": 0.5,
            "maximin_success": 0.5
        }
    }

if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2))
