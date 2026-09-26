from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class FixtureChoice(str, Enum):
    S2_BINDING_RESERVATION = "s2_binding_reservation"
    S2_EXCESS_CAPACITY = "s2_non_guaranteed_excess_capacity"
    L_AMEND = "lender_amend_or_extend"
    L_RESTRICT = "lender_restrict_or_refuse"
    T_SERVE_PRIOR = "transport_serve_prior_commitment"
    T_SERVE_CRITICAL = "transport_serve_critical_current_load"


@dataclass(frozen=True)
class S2TradeoffFixture:
    """Prospective V2 microfixture.

    S2 has a verified outside buyer that can consume 30 units/week. M asks for the frozen
    binding 60/week five-period reservation. No separately frozen premium beyond the existing
    $20k reservation fee exists. A non-guaranteed excess-capacity offer preserves S2's ability
    to serve the outside buyer but gives M no secured capacity.
    """
    outside_buyer_verified: bool = True
    outside_capacity: float = 30.0
    m_binding_capacity: float = 60.0
    reservation_fee_k: float = 20.0


def choose_s2_fixture(regime: str, f: S2TradeoffFixture = S2TradeoffFixture()) -> FixtureChoice:
    # A explicitly preserves the outside option because current availability is not equivalent
    # to committed capacity and the frozen fee does not establish a premium sufficient to erase
    # the verified competing opportunity.
    if regime == "A":
        return FixtureChoice.S2_EXCESS_CAPACITY
    # B0 uses the frozen S2 scalar dimensions. With no quantified profit premium for M, binding
    # capacity creates opportunity/market-loss terms while the $20k fee is only a bounded cash gain.
    if regime.startswith("B"):
        return FixtureChoice.S2_EXCESS_CAPACITY
    # C follows the frozen local order: qualification/contract/cash precede external opportunity.
    # This intentionally demonstrates the consequence of a local priority rule on this fixture.
    return FixtureChoice.S2_BINDING_RESERVATION


@dataclass(frozen=True)
class LenderTradeoffFixture:
    """Prospective V2 lender workout microfixture.

    Both choices are legally available in the discretionary review region. Additional exposure
    materially increases the modeled probability of complete repayment because it preserves the
    borrower's productive recovery corridor. Values are fixture inputs, not empirical bank data.
    """
    headroom: float = 0.35
    current_exposure_k: float = 400.0
    additional_exposure_k: float = 100.0
    repay_probability_restrict: float = 0.42
    repay_probability_amend: float = 0.55
    continuity_restrict: float = 0.20
    continuity_amend: float = 0.90


def choose_lender_fixture(regime: str, f: LenderTradeoffFixture = LenderTradeoffFixture()) -> FixtureChoice:
    if not (0.25 <= f.headroom < 0.45):
        raise ValueError("fixture must lie in discretionary lender-review region")
    if regime == "A":
        # A treats the repayment-generating productive system and added exposure as distinct
        # governing facts; the amendment preserves an adequate repayment corridor in this fixture.
        return FixtureChoice.L_AMEND
    if regime.startswith("B"):
        # Frozen B lender dimensions represented transparently as expected loss + liquidity/
        # covenant burden - continuity benefit. The normalization constants are part of this
        # predeclared microfixture only and are not used as a global benchmark score.
        from .controllers import BASE_B_WEIGHTS
        w = BASE_B_WEIGHTS[__import__('pvpp_benchmark.model', fromlist=['Role']).Role.L]
        def score(amend: bool) -> float:
            p = f.repay_probability_amend if amend else f.repay_probability_restrict
            exposure = f.current_exposure_k + (f.additional_exposure_k if amend else 0.0)
            credit_loss = (1.0-p) * exposure / 500.0
            covenant = max(0.0, 0.45-f.headroom) / 0.20 + (0.20 if amend else 0.0)
            liquidity = (f.additional_exposure_k/500.0) if amend else 0.0
            workout = 0.20 if amend else 0.0
            forgone_return = 0.0 if amend else 0.10
            continuity = 1.0-(f.continuity_amend if amend else f.continuity_restrict)
            return (w['credit_loss']*credit_loss + w['covenant']*covenant + w['liquidity']*liquidity +
                    w['workout']*workout + w['return']*forgone_return + w['continuity']*continuity)
        return FixtureChoice.L_AMEND if score(True) < score(False) else FixtureChoice.L_RESTRICT
    # C local priority puts immediate credit loss before covenant/workout. On this fixture,
    # the amendment sharply improves complete-repayment probability, so it supports the workout.
    return FixtureChoice.L_AMEND


@dataclass(frozen=True)
class TransportTradeoffFixture:
    """Prospective V2 capacity-conflict microfixture.

    T has one feasible service slot and two otherwise feasible loads. One is an earlier accepted
    ordinary commitment; the other is a current expedited load whose non-service creates a severe
    downstream shortage. Accepted service levels remain targets, not guarantees.
    """
    slots: int = 1
    prior_commitment: bool = True
    critical_current_shortage: bool = True


def choose_transport_fixture(regime: str, f: TransportTradeoffFixture = TransportTradeoffFixture()) -> FixtureChoice:
    if f.slots != 1 or not f.prior_commitment or not f.critical_current_shortage:
        raise ValueError("fixture is defined for one-slot prior-vs-critical conflict")
    if regime == "A":
        # Integrated PV-PP framing recognizes the current load's critical downstream productive
        # consequence and can choose it despite the earlier service target.
        return FixtureChoice.T_SERVE_CRITICAL
    # B0's reservation/service terms and C's frozen reserved-capacity-before-service ordering both
    # preserve the prior accepted commitment in this fixture.
    return FixtureChoice.T_SERVE_PRIOR
