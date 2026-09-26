# PV-PP Benchmark V2 — M11 Build Status

Status: PRIMARY EXECUTION CANDIDATE

M11 prospectively repairs D7 and implements the D8 fixture closure before primary outcome inspection.

Quality pipeline:
- conserved S1 clean / latent-defect / suspect / shortcut-reworked / full-reworked provenance
- frozen incoming inspection rates and 0.90 sensitivity / 0.99 specificity
- rework requires and consumes suspect substrate one-for-one
- shortcut rework immediate; full rework delayed one period
- field risk instantiated only when a risk-bearing board enters a delivered finished unit
- ordinary escaped true defect p=0.20; shortcut p=0.08; full rework p=0.015
- semantic event-keyed CRN, no regime identifier in field-risk key

Validation:
- pytest: 114/114 PASS
- M11 Q1-Q10: PASS
- production readiness: 40/40 PASS
- A/B root action-surface parity: 100%
- max transition evaluations observed: 9600 / 10000
- primary outcomes generated during readiness: false

M8-M10 outcomes remain diagnostic only and were not used to choose D8.
