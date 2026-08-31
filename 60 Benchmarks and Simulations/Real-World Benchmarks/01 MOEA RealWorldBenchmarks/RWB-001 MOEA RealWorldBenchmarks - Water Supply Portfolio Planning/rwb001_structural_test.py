
import json, math
from dataclasses import dataclass
from typing import Dict

@dataclass
class Portfolio:
    name: str
    rights: float
    option_low: float
    option_high: float
    xi: float
    alpha_ja: float
    beta_ja: float
    alpha_md: float
    beta_md: float
    cost: float
    reliability: float
    surplus: float
    dropped: float
    leases: float
    costvar: float
    critical_reliability: float
    drought_reliability: float
    scalar_score: float = 0.0

def constraints(p: Portfolio) -> Dict[str, bool]:
    return {
        "reliability_ge_0_98": p.reliability >= 0.98,
        "costvar_le_1_10": p.costvar <= 1.10,
        "critical_reliability_ge_0_99": p.critical_reliability >= 0.99,
        "drought_reliability_eq_1_00": math.isclose(p.drought_reliability, 1.0, abs_tol=1e-12),
    }

def adequate(p: Portfolio) -> bool:
    return all(constraints(p).values())

portfolios = [
    Portfolio("Rights-heavy feasible", 58000, 4000, 8000, .25, 1.0, 1.2, 1.0, 1.2,
              1.60, .995, 18000, 1200, 1.5, 1.05, .997, 1.00),
    Portfolio("Market-heavy feasible", 34000, 9000, 18000, .20, 1.3, 1.8, 1.2, 1.9,
              .78, .991, 6500, 7200, 7.0, 1.09, .994, 1.00),
    Portfolio("Cheap but catastrophic", 30000, 1000, 2000, .10, .6, .8, .5, .7,
              .42, .970, 2500, 800, 2.0, 1.02, .940, .91),
    Portfolio("No-full-adequacy fallback", 32000, 6000, 12000, .20, 1.1, 1.5, 1.0, 1.6,
              .68, .979, 5000, 5000, 5.0, 1.08, .988, .99),
]

results = {}
decision_fields = ["rights","option_low","option_high","xi","alpha_ja","beta_ja","alpha_md","beta_md"]
objective_fields = ["cost","reliability","surplus","dropped","leases"]
constraint_fields = ["costvar","critical_reliability","drought_reliability"]

results["T1_representation_fidelity"] = (
    len(decision_fields) == 8 and len(objective_fields) == 5 and
    all(hasattr(portfolios[0], f) for f in decision_fields + objective_fields + constraint_fields)
)

cheap = portfolios[2]
results["T2_constraint_before_preference"] = (
    cheap.cost < portfolios[0].cost and cheap.cost < portfolios[1].cost and not adequate(cheap)
)

rh, mh = portfolios[0], portfolios[1]
results["T3_persistent_capacity_vs_transaction"] = (
    rh.rights > mh.rights and rh.leases < mh.leases
)

results["T4_uncertainty_information"] = (
    len({rh.reliability, rh.critical_reliability, rh.drought_reliability}) >= 2
)

results["T5_disjoint_families_retained"] = (
    adequate(rh) and adequate(mh) and rh.rights > mh.rights and rh.cost > mh.cost
)

rh.scalar_score = -rh.cost
mh.scalar_score = -mh.cost
results["T6_scalar_containment"] = (
    adequate(rh) and adequate(mh) and mh.scalar_score > rh.scalar_score
)

infeasible_set = [portfolios[2], portfolios[3]]
fallback = max(infeasible_set, key=lambda p: (p.critical_reliability, p.drought_reliability, p.reliability, -p.cost))
results["T7_fallback_without_false_adequacy"] = (
    not any(adequate(p) for p in infeasible_set) and not adequate(fallback)
)

assert all(results.values()), results

payload = {
    "qualification": "source-derived structural mechanism test; not native LRGV simulator execution",
    "constraints_used": {
        "10yr_reliability": ">= 0.98",
        "cost_variability": "<= 1.10",
        "10yr_critical_reliability": ">= 0.99",
        "drought_reliability": "== 1.00"
    },
    "tests": results,
    "passed": sum(results.values()),
    "total": len(results),
    "portfolios": [
        {
            "name": p.name,
            "adequate": adequate(p),
            "constraints": constraints(p),
            "cost": p.cost,
            "reliability": p.reliability,
            "critical_reliability": p.critical_reliability,
            "drought_reliability": p.drought_reliability,
            "rights": p.rights,
            "leases": p.leases
        } for p in portfolios
    ],
    "fallback_selected": fallback.name,
    "fallback_is_adequate": adequate(fallback)
}
print(json.dumps(payload, indent=2))
