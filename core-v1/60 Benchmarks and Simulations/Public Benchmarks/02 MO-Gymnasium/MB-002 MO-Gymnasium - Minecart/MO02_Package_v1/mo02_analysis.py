import itertools, math, json
from math import ceil
from pathlib import Path
import numpy as np
from scipy.stats import norm
from scipy.spatial import ConvexHull
from scipy.optimize import linprog

ROTATION=10
FUEL_MINE=-0.05
FUEL_ACC=-0.025
FUEL_IDLE=-0.005
ACT_MINE=0; ACT_LEFT=1; ACT_RIGHT=2; ACT_ACCEL=3; ACT_BRAKE=4; ACT_NONE=5
FUEL_LIST=[FUEL_MINE+FUEL_IDLE,FUEL_IDLE,FUEL_IDLE,FUEL_IDLE+FUEL_ACC,FUEL_IDLE,FUEL_IDLE]
MINE_RADIUS=0.14; BASE_RADIUS=0.15; BASE_SCALE=1.0; MINE_SCALE=1.0; CART_SCALE=1.0
ACCELERATION=0.0075*CART_SCALE
HOME_POS=np.array([0.0,0.0])
FRAME_SKIP=4
INCREMENTAL=True

CONFIG={
 "capacity":1.5,"mine_cnt":5,"ore_cnt":2,
 "mines":[
  {"x":0.16,"y":0.84,"distributions":[[0.2,0.05],[0,0.05]]},
  {"x":0.5,"y":0.84,"distributions":[[0.15,0.05],[0.1,0.05]]},
  {"x":0.84,"y":0.84,"distributions":[[0.2,0.05],[0.2,0.05]]},
  {"x":0.84,"y":0.5,"distributions":[[0.1,0.05],[0.15,0.05]]},
  {"x":0.84,"y":0.16,"distributions":[[0,0.05],[0.2,0.05]]}
 ]}

def mag(v): return np.sqrt(np.dot(v,v))
def compute_angle(p0,p1,p2):
 v0=np.array(p0)-np.array(p1); v1=np.array(p2)-np.array(p1)
 return np.degrees(np.arctan2(np.linalg.det(np.array([v0,v1])),np.dot(v0,v1)))
def truncated_mean(mean,std,a=0,b=float('inf')):
 if std==0:return mean
 aa=(a-mean)/std; bb=(b-mean)/std
 PHIB=norm.cdf(bb); PHIA=norm.cdf(aa); phib=norm.pdf(bb); phia=norm.pdf(aa)
 return mean+((phia-phib)/(PHIB-PHIA))*std

def pareto_filter(points):
 pts=np.asarray(points,float)
 keep=[]
 for i,p in enumerate(pts):
  dominated=False
  for j,q in enumerate(pts):
   if i!=j and np.all(q>=p-1e-12) and np.any(q>p+1e-12):
    dominated=True;break
  if not dominated: keep.append(i)
 return keep

def candidate_rewards(gamma=1.0,symmetric=True):
 all_rewards=[]; meta=[]
 capacity=CONFIG['capacity']
 # Include virtual empty mine just outside base, as source does
 mines=[(np.array([m['x'],m['y']]),m['distributions'],f"mine{i+1}") for i,m in enumerate(CONFIG['mines'])]
 virtual_pos=np.array([(BASE_RADIUS**2/2)**0.5]*2)
 mines.append((virtual_pos,[[0,0],[0,0]],'virtual_empty'))
 for pos,dists,name in mines:
  mine_distance=mag(pos-HOME_POS)-MINE_RADIUS*MINE_SCALE-BASE_RADIUS*BASE_SCALE/2
  angle=compute_angle(pos,HOME_POS,[1,1])
  rotations=int(ceil(abs(angle)/(ROTATION*FRAME_SKIP)))
  queue=[{"speed":ACCELERATION*FRAME_SKIP,"dist":mine_distance-FRAME_SKIP*(FRAME_SKIP+1)/2*ACCELERATION,"seq":[ACT_ACCEL]}]
  trimmed=[]
  while queue:
   seq=queue.pop()
   ns=seq['speed']+ACCELERATION*FRAME_SKIP
   accels=ns/ACCELERATION
   movement=(accels*(accels+1)/2*ACCELERATION-(accels-FRAME_SKIP)*((accels-FRAME_SKIP)+1)/2*ACCELERATION)
   dist=seq['dist']-movement
   if dist<=0: trimmed.append(seq['seq']+[ACT_ACCEL])
   else: queue.append({'speed':ns,'dist':dist,'seq':seq['seq']+[ACT_ACCEL]})
   dist=seq['dist']-seq['speed']*FRAME_SKIP
   if dist<=0: trimmed.append(seq['seq']+[ACT_NONE])
   else: queue.append({'speed':seq['speed'],'dist':dist,'seq':seq['seq']+[ACT_NONE]})
  means=np.array([truncated_mean(m,s) for m,s in dists])*FRAME_SKIP
  mn_sum=means.sum()
  max_mine=0 if mn_sum==0 else int(ceil(capacity/mn_sum))
  mine_seqs=[[ACT_MINE]*i for i in range(1,max_mine+1)]
  if mine_seqs:
   if symmetric:
    seqs=map(lambda z:list(z[0])+list(z[1])+list(z[2])+list(z[3])+list(z[1]),
      itertools.product([[ACT_LEFT]*rotations],trimmed,[[ACT_BRAKE]+[ACT_LEFT]*(180//(ROTATION*FRAME_SKIP))],mine_seqs))
   else: raise NotImplementedError
  else:
   if symmetric:
    seqs=map(lambda z:list(z[0])+list(z[1])+list(z[2])+[ACT_NONE]+list(z[1][1:]),
      itertools.product([[ACT_LEFT]*rotations],trimmed,[[ACT_LEFT]*(180//(ROTATION*FRAME_SKIP))]))
   else: raise NotImplementedError
  fuel_costs=np.array([f*FRAME_SKIP for f in FUEL_LIST])
  for s in seqs:
   reward=np.zeros((len(s),3)); reward[:,-1]=fuel_costs[s]
   mine_actions=s.count(ACT_MINE)
   if mine_actions:
    reward[-1,:2]=means*mine_actions/max(1,(mn_sum*mine_actions)/capacity)
   disc=gamma**np.arange(len(s))
   R=np.dot(disc,reward)
   all_rewards.append(R); meta.append({'mine':name,'actions':len(s),'mine_actions':mine_actions,'reward':R.tolist()})
 idx=pareto_filter(all_rewards)
 return np.array(all_rewards),meta,idx

def supported_by_grid(pf,steps=101):
 # nonnegative ore weights + nonnegative weight on fuel reward (fuel is negative); simplex w sum=1
 supported=set(); witnesses={}
 for a in np.linspace(0,1,steps):
  for b in np.linspace(0,1-a,steps):
   c=1-a-b
   w=np.array([a,b,c])
   vals=pf@w; mx=vals.max()
   for i,v in enumerate(vals):
    if abs(v-mx)<1e-9:
     supported.add(i); witnesses.setdefault(i,w.tolist())
 return supported,witnesses

if __name__=='__main__':
 allr,meta,idx=candidate_rewards(1.0,True)
 pf=allr[idx]
 # deduplicate near-identical PF vectors, preserve representative metadata
 uniq=[]; u_meta=[]
 for j,i in enumerate(idx):
  p=allr[i]
  if not any(np.allclose(p,q,atol=1e-10) for q in uniq):
   uniq.append(p); u_meta.append(meta[i])
 pf=np.array(uniq)
 supp,wit=supported_by_grid(pf,201)
 exact_supported=[]
 exact_witness={}
 for ii,pp in enumerate(pf):
  A=pf-pp
  lp=linprog(c=np.zeros(3), A_ub=A, b_ub=np.zeros(len(pf)), A_eq=np.ones((1,3)), b_eq=[1], bounds=[(0,None)]*3, method="highs")
  if lp.success:
   exact_supported.append(ii)
   exact_witness[ii]=lp.x.tolist()
 # exact CCS via convex hull with dominated origin trick, as source concept; report grid support as robust check
 out={
  'total_candidates':len(allr),'pareto_unique_count':len(pf),'supported_exact_count':len(exact_supported),'supported_grid_count':len(supp),
  'pareto_points':[]
 }
 for i,(p,m) in enumerate(zip(pf,u_meta)):
  out['pareto_points'].append({'index':i,'reward':p.tolist(),'mine':m['mine'],'actions':m['actions'],'mine_actions':m['mine_actions'],'exact_supported':i in exact_supported,'exact_weight_witness':exact_witness.get(i),'grid_supported':i in supp,'grid_weight_witness':wit.get(i)})
 # standard preference probes
 weights={
  'ore1_priority':[0.70,0.20,0.10],
  'balanced_ores':[0.45,0.45,0.10],
  'ore2_priority':[0.20,0.70,0.10],
  'fuel_sensitive_balanced':[0.30,0.30,0.40],
  'fuel_dominant':[0.10,0.10,0.80],
 }
 out['probes']={}
 for name,w in weights.items():
  w=np.array(w); vals=pf@w; k=int(np.argmax(vals))
  out['probes'][name]={'weights':w.tolist(),'index':k,'reward':pf[k].tolist(),'score':float(vals[k]),'mine':u_meta[k]['mine']}
 path=Path('/mnt/data/mo02_minecart/mo02_result.json'); path.write_text(json.dumps(out,indent=2))
 print(json.dumps(out,indent=2))
