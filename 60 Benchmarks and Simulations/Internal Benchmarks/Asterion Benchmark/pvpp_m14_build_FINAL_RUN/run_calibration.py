from __future__ import annotations
import json
from pathlib import Path
from pvpp_benchmark.calibration import generate_master_seeds, choose_ensemble_n

if __name__ == '__main__':
    seeds=generate_master_seeds(1000)
    n,diag,ref=choose_ensemble_n(seeds)
    print(json.dumps({
        'selected_n':n,
        'max_abs_difference_by_n':{str(k):max(v.values()) for k,v in diag.items()},
        'reference_frequencies':ref,
        'primary_comparative_execution':False,
    },indent=2,sort_keys=True))
