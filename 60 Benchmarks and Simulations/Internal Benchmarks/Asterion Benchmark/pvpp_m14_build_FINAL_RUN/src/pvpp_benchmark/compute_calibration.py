from __future__ import annotations
from dataclasses import asdict
from .world import AsterionWorld
from .model import Role
from .planning import ProjectionBudget, PVPPControllerA, ScalarControllerB
from .calibration import choose_compute_ceiling


def _fixture_worlds(n: int=40):
    rows=[]
    for i in range(n):
        w=AsterionWorld(10_000+i)
        # Controller-neutral calibration states: calm plus bounded hand-solvable
        # deterioration; never the primary challenge trace.
        if i%4==1:
            w.state.period=3; w.deteriorate_s1(3,10,15); w.s1_message(3)
        elif i%4==2:
            w.state.period=4; w.deteriorate_s1(4,15,20); w.s1_message(4)
        elif i%4==3:
            w.state.period=5; w.deteriorate_s1(5,20,25); w.s1_message(5)
        rows.append(w)
    return rows


def run_compute_calibration(n: int=40):
    a_pass={}; b_pass={}; details={}
    for m in (1,2,4):
        budget=ProjectionBudget(10_000*m,2.0*m,256*m,4)
        ap=bp=0; ad=[]; bd=[]
        for w in _fixture_worlds(n):
            p=w.packet(Role.M)
            a=PVPPControllerA(budget).decide(p)
            b=ScalarControllerB(budget,"B0").decide(p)
            aok=not a.budget_exhausted and a.evaluated_count==a.candidate_count
            bok=not b.budget_exhausted and b.evaluated_count==b.candidate_count
            ap+=aok; bp+=bok; ad.append(asdict(a)); bd.append(asdict(b))
        a_pass[m]=ap/n; b_pass[m]=bp/n
        details[m]={"a":ad,"b":bd}
    selected=choose_compute_ceiling(a_pass,b_pass)
    return {"selected":asdict(selected),"a_pass":a_pass,"b_pass":b_pass,"details":details}
