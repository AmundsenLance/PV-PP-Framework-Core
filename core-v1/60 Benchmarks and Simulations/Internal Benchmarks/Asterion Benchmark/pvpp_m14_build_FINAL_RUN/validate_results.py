from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'primary_v2_results'
SEEDS=json.loads((ROOT/'config'/'master_seeds_1000.json').read_text())
REGIMES=['A','B0','B1','B2','B3','B4','C']
errors=[]; count=0
for i,seed in enumerate(SEEDS):
    p=OUT/f'seed_{i:04d}.json'
    if not p.exists():
        errors.append(f'missing {i:04d}'); continue
    try: d=json.loads(p.read_text())
    except Exception as e:
        errors.append(f'unreadable {i:04d}: {e}'); continue
    count+=1
    if d.get('seed_index')!=i or int(d.get('seed'))!=int(seed): errors.append(f'seed mismatch {i:04d}')
    rs=[r.get('regime') for r in d.get('records',[])]
    if rs!=REGIMES: errors.append(f'regime mismatch {i:04d}: {rs}')
fail=OUT/'failures.jsonl'
fail_lines=[]
if fail.exists(): fail_lines=[x for x in fail.read_text().splitlines() if x.strip()]
print(f'Complete seed files: {count}/1000')
print(f'Regime-runs represented: {count*7}/7000')
print(f'Failure records: {len(fail_lines)}')
print(f'Structural errors: {len(errors)}')
for x in errors[:20]: print(' -',x)
if count==1000 and not fail_lines and not errors:
    print('VALIDATION: PASS')
else:
    print('VALIDATION: INCOMPLETE/FAIL')
