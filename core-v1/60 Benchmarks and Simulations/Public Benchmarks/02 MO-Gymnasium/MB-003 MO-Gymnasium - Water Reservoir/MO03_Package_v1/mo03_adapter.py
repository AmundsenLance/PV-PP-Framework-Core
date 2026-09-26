import numpy as np

S=1.0
W_IRR=50.0
H_FLO_U=50.0
S_MIN_REL=100.0
DAM_INFLOW_MEAN=40.0
DAM_INFLOW_STD=10.0
Q_MEF=0.0
GAMMA_H2O=1000.0
W_HYD=4.36
Q_FLO_D=30.0
ETA=1.0
G=9.81

def action_bounds(state):
    lb=max(state-S_MIN_REL,0.0)
    ub=state
    return lb,ub

def step_rewards(state, action, inflow=DAM_INFLOW_MEAN):
    lb,ub=action_bounds(state)
    a=float(np.clip(action,lb,ub))
    n=max(state+inflow-a,0.0)
    r0=-max(n/S-H_FLO_U,0.0)
    r1=-max(W_IRR-a,0.0)
    q=max(a-Q_MEF,0.0)
    p_hyd=ETA*G*GAMMA_H2O*n/S*q/3.6e6
    r2=-max(W_HYD-p_hyd,0.0)
    r3=-max(a-Q_FLO_D,0.0)
    return n,np.array([r0,r1,r2,r3],dtype=float)

def grid_actions(state, step=0.25):
    lb,ub=action_bounds(state)
    n=int(round((ub-lb)/step))
    return np.linspace(lb,ub,n+1)

def scalar_best(state, weights, inflow=DAM_INFLOW_MEAN, step=0.25):
    best=None
    for a in grid_actions(state,step):
        ns,r=step_rewards(state,a,inflow)
        score=float(np.dot(weights,r))
        rec=(score,a,ns,r)
        if best is None or score>best[0]+1e-12 or (abs(score-best[0])<=1e-12 and a<best[1]):
            best=rec
    return best

def zero_adequate_actions(state, domains, inflow=DAM_INFLOW_MEAN, step=0.25, tol=1e-9):
    out=[]
    for a in grid_actions(state,step):
        ns,r=step_rewards(state,a,inflow)
        if all(r[d]>=-tol for d in domains):
            out.append((a,ns,r))
    return out
