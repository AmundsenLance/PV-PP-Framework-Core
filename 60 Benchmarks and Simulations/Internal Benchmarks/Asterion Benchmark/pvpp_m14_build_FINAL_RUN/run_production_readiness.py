from __future__ import annotations
import json, hashlib, platform, sys
from pathlib import Path
from statistics import mean
from pvpp_benchmark.world import AsterionWorld
from pvpp_benchmark.model import Role
from pvpp_benchmark.production import ProductionPVPPControllerA, ProductionScalarControllerB, ProductionLocalControllerC
from pvpp_benchmark.planning import ProjectionBudget

OUT=Path(__file__).parent/'config'/'production_readiness.json'
budget=ProjectionBudget(10_000,2.0,256,4)
rows=[]
for i in range(40):
    seed=10_000+i
    w=AsterionWorld(seed)
    # Controller-neutral perturbations only; no frozen primary challenge sequence.
    w.state.customer_reserve=80+(i%5)*10
    w.state.agents[Role.M].cash_k=300+(i%4)*40
    p=w.packet(Role.M)
    a=ProductionPVPPControllerA(budget).decide(p,seed)
    b=ProductionScalarControllerB(budget,'B0').decide(p,seed)
    c=ProductionLocalControllerC().decide(p,seed)
    a_ids=tuple(x.action.action_id.split('-',3)[-1] for x in a.projected)
    b_ids=tuple(x.action.action_id.split('-',3)[-1] for x in b.projected)
    rows.append({
        'fixture':i,'seed':seed,
        'a_candidates':a.trace.candidate_count,'a_evaluated':a.trace.evaluated_count,'a_evals':a.trace.transition_evaluations,'a_elapsed':a.trace.elapsed_seconds,'a_exhausted':a.trace.budget_exhausted,
        'b_candidates':b.trace.candidate_count,'b_evaluated':b.trace.evaluated_count,'b_evals':b.trace.transition_evaluations,'b_elapsed':b.trace.elapsed_seconds,'b_exhausted':b.trace.budget_exhausted,'b_objective':b.objective_score,
        'same_root_surface':a_ids==b_ids,
        'c_controller':c.trace.controller,
    })
summary={
    'status':'PASS' if all(r['a_evaluated']==r['a_candidates'] and r['b_evaluated']==r['b_candidates'] and not r['a_exhausted'] and not r['b_exhausted'] and r['same_root_surface'] and r['a_elapsed']<=2.0 and r['b_elapsed']<=2.0 for r in rows) else 'FAIL',
    'fixtures':40,
    'budget':{'transition_evaluations':10000,'wall_clock_seconds':2.0,'projection_paths_max':256,'horizon':4},
    'a_pass_fraction':mean([r['a_evaluated']==r['a_candidates'] and not r['a_exhausted'] and r['a_elapsed']<=2.0 for r in rows]),
    'b_pass_fraction':mean([r['b_evaluated']==r['b_candidates'] and not r['b_exhausted'] and r['b_elapsed']<=2.0 for r in rows]),
    'same_root_surface_fraction':mean([r['same_root_surface'] for r in rows]),
    'a_max_evals':max(r['a_evals'] for r in rows),'b_max_evals':max(r['b_evals'] for r in rows),
    'a_max_elapsed':max(r['a_elapsed'] for r in rows),'b_max_elapsed':max(r['b_elapsed'] for r in rows),
    'b_expected_cvar_implemented':all(r['b_objective'] is not None for r in rows),
    'primary_outcomes_generated':False,
    'python':sys.version,'platform':platform.platform(),
}
obj={'summary':summary,'rows':rows}
OUT.write_text(json.dumps(obj,indent=2))
print(json.dumps(summary,indent=2))
