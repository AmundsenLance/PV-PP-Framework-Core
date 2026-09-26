from __future__ import annotations
import json, sys, dataclasses, csv, argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from pvpp_benchmark.production import HomogeneousPrimaryProductionRunner

ap=argparse.ArgumentParser(); ap.add_argument('--start',type=int,default=0); ap.add_argument('--end',type=int,default=1000); args=ap.parse_args()
seeds=json.loads((ROOT/'config'/'master_seeds_1000.json').read_text())
origdir=ROOT/'primary_v2_results'
outdir=ROOT/'a_instrumented_replay'
outdir.mkdir(exist_ok=True)
summary=[]
for i in range(args.start,min(args.end,len(seeds))):
    seed=seeds[i]
    r=HomogeneousPrimaryProductionRunner('A',int(seed),False)
    rec=r.run(through_period=16)
    orig=json.loads((origdir/f'seed_{i:04d}.json').read_text())
    arec=next(x for x in orig['records'] if x['regime']=='A')
    checks={
      'customer_terminated': rec.terminal==arec['terminal'],
      'final_customer_reserve': abs(rec.final_customer_reserve-arec['final_customer_reserve'])<1e-9,
      'final_m_cash_k': abs(rec.final_m_cash_k-arec['final_m_cash_k'])<1e-9,
      'final_s1_line_pp': abs(rec.final_s1_line-arec['final_s1_line'])<1e-9,
      'final_s1_quality_pp': abs(rec.final_s1_quality-arec['final_s1_quality'])<1e-9,
      's2_qualified': rec.s2_qualified==arec['s2_qualified'],
    }
    weekly=[]
    for e in r.world.ledger.entries:
        if e.family=='customer_period_end':
            d=dict(e.payload)
            weekly.append({'period':e.period,'delivered':d.get('delivered'), 'commitment':d.get('commitment'), 'missing':d.get('missing'), 'reserve':d.get('reserve'),'rolling_strikes':d.get('strikes'),'termination_eligible':d.get('termination_eligible'),'terminated':d.get('terminated')})
    # augment from ledger families by period
    byp={w['period']:w for w in weekly}
    for w in weekly:
        p=w['period']; w.update({'s1_recovery':0,'m_assist_s1':0,'transport_book':0,'transport_delay':0,'renegotiation_accepted':0})
    for e in r.world.ledger.entries:
        if e.period in byp:
            w=byp[e.period]
            if e.family in ('s1_recovery','s1_recover','s1_recovery_action'): w['s1_recovery']+=1
            if e.family in ('m_assist_s1','s1_assistance','s1_assist'): w['m_assist_s1']+=1
            if e.family in ('transport_booking','transport_booked'): w['transport_book']+=1
            if 'transport' in e.family and 'delay' in e.family: w['transport_delay']+=1
            if e.family=='renegotiation_accepted': w['renegotiation_accepted']+=1
    # merge state snapshots captured after each period close (period p+1 corresponds end p)
    states={int(s['period'])-1:s for s in r.state_history if int(s['period'])>0}
    for w in weekly:
        s=states.get(w['period'])
        if s:
            pp=s['pp'].get('S1',s['pp'].get('s1',{}))
            w['s1_line_pp']=pp.get('line'); w['s1_quality_pp']=pp.get('quality'); w['m_cash_k']=s['m_cash_k']; w['headroom']=s['headroom']
    payload={'seed_index':i,'seed':int(seed),'reproduces_original':all(checks.values()),'checks':checks,'terminal':{'customer_terminated':rec.terminal,'reserve':rec.final_customer_reserve},'weekly':weekly}
    (outdir/f'seed_{i:04d}.json').write_text(json.dumps(payload,sort_keys=True))
    summary.append({'seed_index':i,'seed':int(seed),'reproduces_original':all(checks.values()),'customer_terminated':rec.terminal,'weeks':len(weekly)})
    if i%50==0: print(i, flush=True)
(Path(outdir/f'summary_{args.start}_{args.end}.json')).write_text(json.dumps(summary,indent=2))
print('DONE',sum(x['reproduces_original'] for x in summary),'/',len(summary))
