#!/bin/bash
set -u
cd "$(dirname "$0")"
mkdir -p primary_v2_results logs
PYBIN="$(command -v python3 || true)"
if [ -z "$PYBIN" ]; then
  echo "Python 3 is required. Install Python 3.11+ and rerun this file."
  read -r -p "Press Enter to close..."
  exit 1
fi
"$PYBIN" - <<'PY'
import sys
if sys.version_info < (3,11):
    raise SystemExit(f"Python 3.11+ required; found {sys.version.split()[0]}")
print("Python",sys.version.split()[0],"OK")
PY
if [ $? -ne 0 ]; then read -r -p "Press Enter to close..."; exit 1; fi

echo "Starting/resuming PV-PP V2 M14 primary ensemble in 8 shards..."
echo "Results remain in: $(pwd)/primary_v2_results"
for s in 0 1 2 3 4 5 6 7; do
  start=$((s*125)); end=$(((s+1)*125))
  "$PYBIN" run_primary_ensemble_v2.py --start "$start" --end "$end" >"logs/shard_${s}.log" 2>&1 &
  pids[$s]=$!
  echo "Shard $s: seeds $start-$((end-1)), PID ${pids[$s]}"
done

status=0
for pid in ${pids[*]}; do wait "$pid" || status=1; done

echo
echo "All shards exited. Running structural validation..."
"$PYBIN" validate_results.py | tee validation.txt

echo
echo "Do not delete this folder. Zip the entire pvpp_m14_build folder or at minimum primary_v2_results + validation.txt and upload it back to ChatGPT for analysis."
read -r -p "Press Enter to close..."
exit $status
