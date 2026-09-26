# PV-PP Asterion Benchmark — M14

This is the clean post-M13-audit production package. M12 remains banked. M13 remains diagnostic and is not overwritten.

The M13 customer-exit calibration and the frozen P16 horizon are unchanged. M14 contains only authority-derived quality-path implementation repairs plus right-censoring reporting.

Run conformance: `PYTHONPATH=src python run_conformance.py`

Run production readiness: `PYTHONPATH=src python run_production_readiness.py`

Run the full 1,000-seed x 7-regime ensemble on macOS: double-click `run_v2_mac.command`.
