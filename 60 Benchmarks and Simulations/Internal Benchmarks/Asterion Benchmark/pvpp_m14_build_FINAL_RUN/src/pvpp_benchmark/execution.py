from __future__ import annotations
from .production import HomogeneousPrimaryProductionRunner

class PrimaryExecutionLocked(RuntimeError): pass

# Authorized by V2 Execution Lock Record v1 (31 August 2026).
# Authorization does not itself start any run.
PRIMARY_COMPARATIVE_EXECUTION=True


def run_primary_single(regime:str,seed:int,deterministic:bool=False,through_period:int=16):
    if not PRIMARY_COMPARATIVE_EXECUTION:
        raise PrimaryExecutionLocked("Primary A/B/C comparative execution is prohibited until the revised Calibration Lock authorizes the production runner.")
    return HomogeneousPrimaryProductionRunner(regime,seed,deterministic).run(through_period)


def run_primary_comparative(seed:int=0,deterministic:bool=False,through_period:int=16,regimes=("A","B0","C")):
    if not PRIMARY_COMPARATIVE_EXECUTION:
        raise PrimaryExecutionLocked("Primary A/B/C comparative execution is prohibited until the revised Calibration Lock authorizes the production runner.")
    return tuple(HomogeneousPrimaryProductionRunner(r,seed,deterministic).run(through_period) for r in regimes)
