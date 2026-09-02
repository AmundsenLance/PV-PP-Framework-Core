from __future__ import annotations
import argparse, dataclasses, json, os, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))
from pvpp_benchmark.execution import run_primary_comparative

REGIMES = ("A","B0","B1","B2","B3","B4","C")

def atomic_write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, sort_keys=True)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, required=True)
    ap.add_argument('--end', type=int, required=True, help='exclusive seed index')
    ap.add_argument('--out', default='primary_v2_results')
    args = ap.parse_args()
    seeds = json.loads((ROOT/'config'/'master_seeds_1000.json').read_text())
    out = ROOT/args.out
    out.mkdir(parents=True, exist_ok=True)
    fail = out/'failures.jsonl'
    for i in range(args.start, min(args.end, len(seeds))):
        p = out/f'seed_{i:04d}.json'
        if p.exists():
            print(f'SKIP {i:04d}', flush=True); continue
        seed = int(seeds[i]); t0=time.time()
        try:
            recs = run_primary_comparative(seed=seed, deterministic=False, through_period=16, regimes=REGIMES)
            payload = {'seed_index':i,'seed':seed,'regimes':list(REGIMES),'records':[dataclasses.asdict(r) for r in recs]}
            atomic_write_json(p,payload)
            print(f'DONE {i:04d} {time.time()-t0:.2f}s', flush=True)
        except Exception as e:
            with fail.open('a',encoding='utf-8') as f:
                f.write(json.dumps({'seed_index':i,'seed':seed,'error':repr(e)})+'\n')
            print(f'FAIL {i:04d}: {e!r}', file=sys.stderr, flush=True)

if __name__=='__main__': main()
