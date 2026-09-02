PV-PP V2 M14 LOCAL PRIMARY RUN
Prepared after the pre-banking M13 quality-path audit. M13 remains diagnostic evidence and is not overwritten.

1. Keep this entire pvpp_m14_build folder together.
2. Double-click run_v2_mac.command. macOS may require right-click -> Open the first time.
3. Leave Terminal open while it runs.
4. The job uses eight independent shards and the unchanged frozen 1,000-seed list.
5. Every completed seed is atomically saved in primary_v2_results/.
6. If interrupted, run the command again; completed seed files are skipped.
7. At completion validation.txt must report 1000/1000 seed files, 7000/7000 regime-runs, 0 failures, 0 structural errors, VALIDATION: PASS.
8. Zip the whole pvpp_m14_build folder (or primary_v2_results plus validation.txt) and upload it for paired analysis.

M14 preserves the M13 customer-exit calibration and P16 horizon. The production package contains no M13 production outputs.
Requires Python 3.11+; no third-party runtime packages are required.
