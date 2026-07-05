import math

import pytest

from bot.strategy import Pools, decide, diluted_ev, naive_ev, payout_multiplier


def test_payout_matches_contract_formula():
    # rewardAmount = total * (1 - fee); winner of 1 unit gets rewardAmount / winnerPool.
    assert payout_multiplier(total=10.0, side_pool=4.0, fee=0.03) == pytest.approx(
        10.0 * 0.97 / 4.0
    )


def test_even_odds_ev_is_minus_fee():
    # Balanced pools: multiplier = 2 * (1 - fee), so EV at p = 0.5 is exactly -fee.
    assert naive_ev(total=2.0, side_pool=1.0, fee=0.03) == pytest.approx(-0.03)


def test_empty_side_pool_raises():
    with pytest.raises(ValueError):
        payout_multiplier(total=5.0, side_pool=0.0)


def test_dilution_lowers_ev():
    pools = Pools(bull=1.0, bear=3.0)
    undiluted = naive_ev(pools.total, pools.bull, fee=0.0)
    diluted = diluted_ev(pools, "bull", stake=1.0, fee=0.0)
    assert undiluted == pytest.approx(1.0)  # 0.5 * 4/1 - 1
    assert diluted == pytest.approx(0.25)  # 0.5 * 5/2 - 1
    assert diluted < undiluted


def test_dilution_monotone_in_stake():
    pools = Pools(bull=2.0, bear=10.0)
    evs = [diluted_ev(pools, "bull", stake=s) for s in (0.01, 0.1, 1.0, 10.0)]
    assert all(a > b for a, b in zip(evs, evs[1:], strict=False))


def test_decide_picks_underdog_above_threshold():
    # Bear pool is a third of bull's: bear multiplier ~ 2.9, naive EV ~ +0.46.
    pools = Pools(bull=3.0, bear=1.0)
    assert decide(pools, threshold=0.25) == "bear"


def test_decide_returns_none_when_balanced():
    pools = Pools(bull=1.0, bear=1.0)
    assert decide(pools, threshold=0.05) is None  # both sides EV = -fee


def test_decide_threshold_boundary():
    pools = Pools(bull=3.0, bear=1.0)
    ev_bear = naive_ev(4.0, 1.0)
    assert decide(pools, threshold=ev_bear) == "bear"  # >= comparison
    assert decide(pools, threshold=ev_bear + 1e-9) is None


def test_decide_empty_side_without_stake_is_infinite_ev():
    pools = Pools(bull=1.0, bear=0.0)
    assert decide(pools, threshold=100.0) == "bear"


def test_decide_empty_side_with_stake_uses_dilution():
    pools = Pools(bull=1.0, bear=0.0)
    # Staking 1 into the empty side: multiplier = 2 * 0.97 / 1, EV = -0.03.
    assert diluted_ev(pools, "bear", stake=1.0) == pytest.approx(-0.03)
    assert decide(pools, threshold=0.25, stake=1.0) is None


def test_decide_empty_round():
    assert decide(Pools(bull=0.0, bear=0.0), threshold=0.0) is None
    # Pinned by design: an empty round carries no odds information, so it is
    # skipped even when a stake would make the diluted EV well-defined.
    assert decide(Pools(bull=0.0, bear=0.0), threshold=-0.9, stake=0.1) is None


def test_naive_ev_scale_invariance():
    # Same pool ratio in BNB or wei must give the same EV.
    assert naive_ev(4.0, 1.0) == pytest.approx(naive_ev(4e18, 1e18))
    assert not math.isnan(naive_ev(4.0, 1.0))
