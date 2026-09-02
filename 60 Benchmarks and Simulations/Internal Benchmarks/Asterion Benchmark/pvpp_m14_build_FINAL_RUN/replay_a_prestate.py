from __future__ import annotations
import json,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner, ProductionDecision, ProductionRolePolicy, _routine_flow_from_packet
from pvpp_benchmark.model import Action, ActionKind, Role
from pvpp_benchmark.planning import DecisionTrace

ap=argparse.ArgumentParser(); ap.add_argument('--start',type=int,required=True); ap.add_argument('--end',type=int,required=True); a=ap.parse_args()
seeds=json.loads((ROOT/'config'/'master_seeds_1000.json').read_text()); origdir=ROOT/'primary_v2_results'; outdir=ROOT/'a_prestate_replay'; outdir.mkdir(exist_ok=True)
class FixedMController:
    def __init__(self, period_actions): self.period_actions=period_actions
    def decide(self, packet, seed):
        d=self.period_actions[packet.period]; ad=d['action']; chosen=Action(ad['action_id'],Role(ad['actor']),ActionKind(ad['kind']),dict(ad.get('params') or {}),Role(ad['target']) if ad.get('target') else None)
        tr=DecisionTrace('A-REPLAY',Role.M,packet.period,chosen,d.get('candidate_count',0),d.get('evaluated_count',0),d.get('transition_evaluations',0),0.0,False,('INSTRUMENTED_REPLAY',))
        return ProductionDecision(tr,(),None,_routine_flow_from_packet(packet,chosen)+(chosen,))
class CaptureC:
    def __init__(self,base,store): self.base=base; self.store=store
    def decide_bundle(self,packet,seed):
        self.store[packet.period]={
          'pre_reserve':float(packet.direct_observations.get('customer_reserve',0)),
          'pre_termination_eligible':bool(packet.direct_observations.get('termination_eligible',False)),
          'pre_strikes':int(packet.direct_observations.get('breach_strikes',0) or 0),
        }
        tr,b=self.base.decide_bundle(packet,seed)
        self.store[packet.period]['c_action']=tr.action.kind.value
        return tr,b
for i in range(a.start,min(a.end,len(seeds))):
    seed=seeds[i]; orig=json.loads((origdir/f'seed_{i:04d}.json').read_text()); arec=next(x for x in orig['records'] if x['regime']=='A')
    macts={int(t['period']):t for t in arec['decision_traces'] if t['role']=='M'}
    r=HomogeneousPrimaryProductionRunner('A',int(seed),False); r.m_controller=FixedMController(macts)
    cstore={}; r.role_controllers[Role.C]=CaptureC(r.role_controllers[Role.C],cstore)
    rec=r.run(through_period=16)
    checks={'terminal':rec.terminal==arec['terminal'],'reserve':abs(rec.final_customer_reserve-arec['final_customer_reserve'])<1e-9,'cash':abs(rec.final_m_cash_k-arec['final_m_cash_k'])<1e-9,'s1_line':abs(rec.final_s1_line-arec['final_s1_line'])<1e-9,'s1_quality':abs(rec.final_s1_quality-arec['final_s1_quality'])<1e-9,'s2_qualified':rec.s2_qualified==arec['s2_qualified']}
    weekly=[]; byp={}
    for e in r.world.ledger.entries:
      if e.family=='customer_period_end':
        d=e.payload; w={'period':e.period,'delivered':d.get('delivered'),'commitment':d.get('commitment'),'missing':d.get('missing'),'end_reserve':d.get('reserve'),'end_rolling_strikes':d.get('strikes'),'end_termination_eligible':d.get('termination_eligible'),'terminated':d.get('terminated')}; w.update(cstore.get(e.period,{})); weekly.append(w); byp[e.period]=w
    for e in r.world.ledger.entries:
      w=byp.get(e.period)
      if not w: continue
      if e.family=='s1_recovery': w['s1_recovery']=w.get('s1_recovery',0)+1
      if 'assist' in e.family and 's1' in e.family: w['m_assist_s1']=w.get('m_assist_s1',0)+1
      if 'transport' in e.family and ('booking' in e.family or 'book' in e.family): w['transport_book']=w.get('transport_book',0)+1
      if 'transport' in e.family and 'delay' in e.family: w['transport_delay']=w.get('transport_delay',0)+1
    payload={'seed_index':i,'seed':int(seed),'reproduces_original':all(checks.values()),'checks':checks,'customer_terminated':rec.terminal,'weekly':weekly}
    (outdir/f'seed_{i:04d}.json').write_text(json.dumps(payload,sort_keys=True))
print('done',a.start,a.end)
