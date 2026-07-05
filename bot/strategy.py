"""Parimutuel strategy math for PancakeSwap Prediction.

Everything here is a pure function of pool sizes, so the decision logic is
unit-testable without touching the chain. Amounts can be in any consistent
unit (BNB or wei).

Contract payout (PancakePredictionV2): a winning stake is paid

    stake * rewardAmount / rewardBaseCalAmount

where ``rewardAmount = totalAmount * (1 - fee)`` and ``rewardBaseCalAmount``
is the winning side's pool. The payout includes the stake itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Side = Literal["bull", "bear"]

#: Treasury fee of PancakePredictionV2 (300/10000 at deployment; verified
#: empirically from round data — see research/metrics.py:fee_stats).
DEFAULT_FEE = 0.03


@dataclass(frozen=True)
class Pools:
    """Bull/bear pool sizes for one round."""

    bull: float
    bear: float

    @property
    def total(self) -> float:
        return self.bull + self.bear


def payout_multiplier(total: float, side_pool: float, fee: float = DEFAULT_FEE) -> float:
    """Gross payout per 1 unit staked on a side, if that side wins.

    Raises ``ValueError`` on an empty side pool: the multiplier is unbounded
    until a stake exists, so callers should evaluate empty sides through
    :func:`diluted_ev` with their intended stake.
    """
    if side_pool <= 0:
        raise ValueError("side pool must be positive; evaluate empty sides via diluted_ev")
    return total * (1.0 - fee) / side_pool


def naive_ev(
    total: float, side_pool: float, fee: float = DEFAULT_FEE, p_win: float = 0.5
) -> float:
    """Expected net return per 1 unit staked, assuming win probability ``p_win``.

    "Naive" because p_win = 0.5 (the random-walk assumption) is exactly the
    hypothesis this project set out to test — and rejected: empirically the
    win rate falls as this number rises.
    """
    return p_win * payout_multiplier(total, side_pool, fee) - 1.0


def diluted_ev(
    pools: Pools,
    side: Side,
    stake: float,
    fee: float = DEFAULT_FEE,
    p_win: float = 0.5,
) -> float:
    """EV per 1 unit staked, accounting for the stake's own price impact.

    Your stake joins both the total and your side's pool, so the realized
    multiplier is ``(total + stake) * (1 - fee) / (side_pool + stake)`` —
    strictly worse than the pre-stake quote. The effect is negligible for
    small stakes but material in thin pools.
    """
    if stake <= 0:
        raise ValueError("stake must be positive")
    side_pool = pools.bull if side == "bull" else pools.bear
    multiplier = (pools.total + stake) * (1.0 - fee) / (side_pool + stake)
    return p_win * multiplier - 1.0


def decide(
    pools: Pools,
    threshold: float,
    fee: float = DEFAULT_FEE,
    stake: float = 0.0,
) -> Side | None:
    """Return the side to bet, or ``None`` when no side clears ``threshold``.

    With ``stake > 0`` the EVs are computed post-dilution (recommended);
    with ``stake == 0`` an empty side quotes an infinite naive EV, which is
    mathematically correct for an infinitesimal stake. A completely empty
    round returns ``None`` by design, regardless of stake: there is no odds
    information to act on.
    """
    if pools.total <= 0:
        return None
    evs: dict[Side, float] = {}
    for side, side_pool in (("bull", pools.bull), ("bear", pools.bear)):
        if stake > 0:
            evs[side] = diluted_ev(pools, side, stake, fee)
        elif side_pool > 0:
            evs[side] = naive_ev(pools.total, side_pool, fee)
        else:
            evs[side] = float("inf")
    if not evs:
        return None
    best = max(evs, key=lambda s: evs[s])
    return best if evs[best] >= threshold else None
