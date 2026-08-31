"""
Reproduce the RWB-001 native comparison against the supplied
MOEAFramework RealWorldBenchmarks LRGV executable.

Run from a checkout containing native/LRGV/bin/lrgv, or edit EXE_DIR.
Uses frozen seed 20260830 and evaluates the same generated candidate set
under both ten-year and combined modes.
"""
import json, math, random, subprocess, time
from pathlib import Path

N = 250
SEED = 20260830
EXE_DIR = Path("native/LRGV/bin")

def transform(vals):
    vals = list(vals)
    v2 = vals[2]
    if v2 < .15: v2=.1
    elif v2 < .25: v2=.2
    elif v2 < .35: v2=.3
    elif v2 < .45: v2=.4
    elif v2 < .55: v2=.5
    elif v2 < .65: v2=.6
    elif v2 < .75: v2=.7
    elif v2 < .85: v2=.8
    elif v2 < .95: v2=.9
    else: v2=1.0
    vals[2]=v2

    v3=vals[3]
    vals[3]=.10 if v3<.125 else .15 if v3<.175 else .20 if v3<.225 else .25 if v3<.275 else .30 if v3<.325 else .35 if v3<.375 else .40

    for j in range(4,8):
        vals[j]=math.floor(vals[j]*100+.5)/100
    if vals[4]+vals[5] > 3.0:
        vals[5]=3.0-vals[4]
    if vals[6]+vals[7] > 3.0:
        vals[7]=3.0-vals[6]
    return vals

def run(mode, points):
    lines = [" ".join(f"{x:.10g}" for x in p) for p in points]
    start=time.time()
    cp=subprocess.run(
        ["./lrgv","-m","std-io","-b","AllDecAll","-c",mode],
        input="\n".join(lines)+"\n",
        text=True, capture_output=True, cwd=EXE_DIR, check=True
    )
    outputs=[list(map(float,l.split())) for l in cp.stdout.strip().splitlines()]
    return outputs, time.time()-start

random.seed(SEED)
points=[]
for _ in range(N):
    raw=[
        random.random(), random.random(), random.uniform(.1,1),
        random.uniform(.1,.4), random.uniform(0,3), random.uniform(0,3),
        random.uniform(0,3), random.uniform(0,3)
    ]
    points.append(transform(raw))

ten, t1 = run("ten-year", points)
combined, t2 = run("combined", points)

def feasible(y):
    return all(abs(c) <= 1e-12 for c in y[6:10])

ten_f=[i for i,y in enumerate(ten) if feasible(y)]
comb_f=[i for i,y in enumerate(combined) if feasible(y)]

result={
    "seed":SEED, "n":N,
    "ten_year_seconds":t1, "combined_seconds":t2,
    "ten_year_feasible":len(ten_f),
    "combined_feasible":len(comb_f),
    "drtranscost_changed":sum(abs(a[5]-b[5])>1e-12 for a,b in zip(ten,combined)),
    "drvuln_constraint_changed":sum(abs(a[9]-b[9])>1e-12 for a,b in zip(ten,combined)),
    "ten_year_false_feasible":sorted(set(ten_f)-set(comb_f)),
    "points":points,
    "ten_year_outputs":ten,
    "combined_outputs":combined
}
Path("rwb001_native_reproduction.json").write_text(json.dumps(result, indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ("points","ten_year_outputs","combined_outputs")}, indent=2))
