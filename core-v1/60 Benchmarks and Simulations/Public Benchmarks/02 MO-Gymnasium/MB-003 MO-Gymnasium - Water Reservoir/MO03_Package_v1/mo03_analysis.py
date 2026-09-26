from mo03_adapter import *
import json

states=[20.,40.,60.,100.,140.]
rows=[]
for s in states:
    all4=zero_adequate_actions(s,[0,1,2,3])
    safety=zero_adequate_actions(s,[0,3])
    sb=scalar_best(s,np.ones(4))
    rows.append({
      'state':s,
      'all4_adequate_count':len(all4),
      'safety_adequate_count':len(safety),
      'safety_interval':[safety[0][0],safety[-1][0]] if safety else None,
      'equal_weight_scalar_action':sb[1],
      'equal_weight_scalar_reward':sb[3].tolist(),
      'equal_weight_scalar_score':sb[0]
    })

# Algebraic contradiction: r1=0 needs a>=50; r3=0 needs a<=30.
contradiction={'water_zero_requires_action_ge':W_IRR,'downstream_zero_requires_action_le':Q_FLO_D,'joint_possible':W_IRR<=Q_FLO_D}

# Mean-inflow safety feasibility analytic boundary: r0=0 -> a >= state+40-50=state-10; r3=0 -> a<=30.
# together feasible iff state <=40, plus action bounds; verify selected states.
result={'source_constants':{
 'W_IRR':W_IRR,'H_FLO_U':H_FLO_U,'S_MIN_REL':S_MIN_REL,'DAM_INFLOW_MEAN':DAM_INFLOW_MEAN,
 'DAM_INFLOW_STD':DAM_INFLOW_STD,'W_HYD':W_HYD,'Q_FLO_D':Q_FLO_D},
 'all4_zero_adequacy_contradiction':contradiction,
 'mean_inflow_safety_boundary_state':40.0,
 'rows':rows}
with open('/mnt/data/mo03_reservoir/mo03_result.json','w') as f: json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
