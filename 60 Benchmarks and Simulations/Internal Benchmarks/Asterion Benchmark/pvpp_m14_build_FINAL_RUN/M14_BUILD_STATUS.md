# PV-PP Benchmark V2 — M14 Build Status

Status: READY FOR NEW PRIMARY ENSEMBLE RUN

M14 is the clean post-audit successor to diagnostic M13. M12 remains the first banked hard benchmark. M13 remains preserved as diagnostic evidence and is not banked.

Frozen M13 customer-exit calibration is unchanged. The P16 horizon is unchanged.

Authority-derived implementation repairs:
- D10: major field-quality events are evaluated from observed attributable failures in rolling two-period delivery cohorts, not from failures becoming due in the current processing period.
- Incoming inspection: event-keyed uniform sampling without replacement; no controller/regime key.
- Stable board identity: physical board IDs persist through inspection, FIFO production, rework, finished-goods shipment, and field-failure risk.
- S1 quality bands: latent defect probability is fixed from valid quality at S1 shipment; no unauthorized q<35 probability exists.
- Sample size: smallest integer meeting the frozen percentage, with frozen minima.
- Dead legacy rework-failure scheduler removed; active field risk is created only at delivery.
- P16 reporting: C operations PP=0 without an executable P17 termination is reported as a right-censored customer business collapse, not a successful survival.

Verification:
- 128/128 conformance tests PASS.
- Production readiness 40/40 PASS.
- A/B root action-surface parity 100%.
- Maximum transition evaluations 9600/10000.
- Two-seed x seven-regime production-path smoke run PASS (outputs removed from clean build).

No repair was selected from observed M13 comparative outcomes.
