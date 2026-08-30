import json, importlib.util, numpy as np
from scipy.optimize import linprog

spec=importlib.util.spec_from_file_location('mo02','/mnt/data/mo02_minecart/mo02_analysis.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
R,meta,idx=m.candidate_rewards(1.0,True)
# dedupe PF
P=[]
for i in idx:
    if not any(np.allclose(R[i],q,atol=1e-10) for q in P): P.append(R[i])
P=np.asarray(P)

def linearly_supported(i):
    A=P-P[i]
    res=linprog(c=np.zeros(3),A_ub=A,b_ub=np.zeros(len(P)),A_eq=np.ones((1,3)),b_eq=[1],bounds=[(0,None)]*3,method='highs')
    return res.success

def unique_adequate(a,b,f):
    ids=np.where((R[:,0]>=a)&(R[:,1]>=b)&(R[:,2]>=f))[0]
    uniq=[]
    for i in ids:
        if not any(np.allclose(R[i],R[j]) for j in uniq): uniq.append(i)
    return uniq

def test_candidate_count(): assert len(R)==154
def test_pareto_count(): assert len(P)==10
def test_four_pareto_points_are_not_linear_weight_supported(): assert sum(not linearly_supported(i) for i in range(len(P)))==4
def test_extreme_ore1_supported(): assert linearly_supported(1)
def test_balanced_supported(): assert linearly_supported(4)
def test_extreme_ore2_supported(): assert linearly_supported(8)
def test_empty_fuel_minimizer_supported(): assert linearly_supported(9)
def test_threshold_case_ore1_unique(): assert len(unique_adequate(.75,.15,-.80))==1
def test_threshold_case_mixed_unique(): assert len(unique_adequate(.55,.40,-.84))==1
def test_threshold_case_ore2_unique(): assert len(unique_adequate(.15,.75,-.80))==1
def test_threshold_case_balanced_unique(): assert len(unique_adequate(.70,.70,-.90))==1
