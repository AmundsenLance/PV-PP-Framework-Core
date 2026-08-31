import random, subprocess, json, math, time
from pathlib import Path
repo=Path('/mnt/data/rwb_repo/RealWorldBenchmarks')
exe=repo/'native/LakeProblem/bin/lake'
SEED=20260830
random.seed(SEED)
policies=[]
labels=[]
# structured policies
struct=[]
struct.append(('zero', [0.0]*100))
for c in [0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10]:
    struct.append((f'constant_{c:.2f}', [c]*100))
struct.append(('ramp_up', [0.1*i/99 for i in range(100)]))
struct.append(('ramp_down', [0.1*(99-i)/99 for i in range(100)]))
struct.append(('step_low_high', [0.02]*50+[0.08]*50))
struct.append(('step_high_low', [0.08]*50+[0.02]*50))
struct.append(('alternating', [0.02 if i%2==0 else 0.08 for i in range(100)]))
struct.append(('smooth_wave', [0.05+0.03*math.sin(2*math.pi*i/20) for i in range(100)]))
for name,p in struct:
    labels.append(name); policies.append(p)
# 500 random walk policies with bounded step to span inertia behavior
for k in range(500):
    x=random.uniform(0,0.1); p=[]
    for i in range(100):
        # mixture of smooth and jumpy
        scale = 0.008 if k<250 else 0.035
        x=max(0,min(0.1,x+random.gauss(0,scale)))
        p.append(x)
    labels.append(f'randomwalk_{k:03d}'); policies.append(p)
# 300 iid policies
for k in range(300):
    p=[random.uniform(0,0.1) for _ in range(100)]
    labels.append(f'iid_{k:03d}'); policies.append(p)

inp='\n'.join(' '.join(f'{x:.12g}' for x in p) for p in policies)+'\n'
cp=subprocess.run([str(exe)],input=inp,text=True,capture_output=True,cwd=exe.parent,check=True)
outs=[list(map(float,l.split())) for l in cp.stdout.strip().splitlines()]
assert len(outs)==len(policies), (len(outs),len(policies))
# outputs maxP(min), expectedBenefit(max), inertia(max), reliability(max), raw reliability constraint
records=[]
for name,p,y in zip(labels,policies,outs):
    records.append({'name':name,'policy':p,'maxP':y[0],'benefit':y[1],'inertia':y[2],'reliability':y[3],'constraint_raw':y[4],'feasible':y[4]>=0.85})
# Pareto among feasible: minimize maxP, maximize others
def dominates(a,b):
    va=[a['maxP'],-a['benefit'],-a['inertia'],-a['reliability']]
    vb=[b['maxP'],-b['benefit'],-b['inertia'],-b['reliability']]
    return all(x<=y+1e-12 for x,y in zip(va,vb)) and any(x<y-1e-12 for x,y in zip(va,vb))
feas=[r for r in records if r['feasible']]
pareto=[]
for i,a in enumerate(feas):
    if not any(i!=j and dominates(b,a) for j,b in enumerate(feas)):
        pareto.append(a)
# find lower maxP feasible vs higher benefit feasible tradeoff
# cheapest analog doesn't fit; benefit vs threshold.
best_benefit=max(feas,key=lambda r:r['benefit']) if feas else None
best_water=min(feas,key=lambda r:r['maxP']) if feas else None
# infeasible high benefit if available
infeas=[r for r in records if not r['feasible']]
high_infeas=max(infeas,key=lambda r:r['benefit']) if infeas else None
summary={
 'seed':SEED,'n':len(records),'structured_n':len(struct),'feasible_n':len(feas),'infeasible_n':len(infeas),'pareto_feasible_sample_n':len(pareto),
 'best_benefit_feasible': {k:best_benefit[k] for k in ['name','maxP','benefit','inertia','reliability']} if best_benefit else None,
 'best_maxP_feasible': {k:best_water[k] for k in ['name','maxP','benefit','inertia','reliability']} if best_water else None,
 'highest_benefit_infeasible': {k:high_infeas[k] for k in ['name','maxP','benefit','inertia','reliability']} if high_infeas else None,
 'structured':[{k:r[k] for k in ['name','maxP','benefit','inertia','reliability','feasible']} for r in records[:len(struct)]],
 'pareto_names':[r['name'] for r in pareto]
}
Path('/mnt/data/rwb002_native_records.json').write_text(json.dumps(records,indent=2))
Path('/mnt/data/rwb002_native_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
