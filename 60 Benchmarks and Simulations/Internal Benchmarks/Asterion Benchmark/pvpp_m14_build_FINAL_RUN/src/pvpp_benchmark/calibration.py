from __future__ import annotations
from dataclasses import dataclass
from .rng import master_seed, SemanticRNG

@dataclass(frozen=True)
class ComputeCalibrationResult:
    multiplier: int | None
    transition_evaluation_ceiling: int | None
    wall_clock_seconds: float | None
    projection_paths: int | None
    passing_fraction_a: float
    passing_fraction_b: float


def choose_compute_ceiling(a_pass: dict[int,float], b_pass: dict[int,float], pass_fraction=.95):
    for m in (1,2,4):
        if a_pass.get(m,0)>=pass_fraction and b_pass.get(m,0)>=pass_fraction:
            return ComputeCalibrationResult(m,10000*m,2.0*m,256*m,a_pass[m],b_pass[m])
    return ComputeCalibrationResult(None,None,None,None,max(a_pass.values(),default=0),max(b_pass.values(),default=0))


def generate_master_seeds(n=1000):
    return [master_seed(i) for i in range(n)]


def controller_free_features(seed: int):
    r=SemanticRNG(seed)
    onset=r.choice([3,4,5],[1/3,1/3,1/3],"s1_onset",0,"S1")
    line=r.choice([10,15,20],[.25,.5,.25],"s1_initial_line",onset,"S1")
    quality=r.choice([15,20,25],[.25,.5,.25],"s1_initial_quality",onset,"S1")
    msg=r.choice(["exact","temporary","optimistic"],[.40,.35,.25],"s1_message",onset,"S1","M")
    return {"onset":onset,"line_dec":line,"quality_dec":quality,"message":msg}


def _freq(rows, key, value):
    return sum(r[key]==value for r in rows)/len(rows)


def choose_ensemble_n(seeds=None, tolerance=.03):
    seeds=generate_master_seeds(1000) if seeds is None else seeds
    full=[controller_free_features(s) for s in seeds[:1000]]
    monitored={
        **{f"onset={v}":("onset",v) for v in (3,4,5)},
        **{f"line={v}":("line_dec",v) for v in (10,15,20)},
        **{f"quality={v}":("quality_dec",v) for v in (15,20,25)},
        **{f"message={v}":("message",v) for v in ("exact","temporary","optimistic")},
    }
    ref={name:_freq(full,*kv) for name,kv in monitored.items()}
    diagnostics={}
    for n in (100,250,500,1000):
        rows=full[:n]
        diffs={name:abs(_freq(rows,*kv)-ref[name]) for name,kv in monitored.items()}
        diagnostics[n]=diffs
        if max(diffs.values())<=tolerance:
            return n,diagnostics,ref
    return 1000,diagnostics,ref
