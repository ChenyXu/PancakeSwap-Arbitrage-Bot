import numpy as np
import pandas as pd
import pytest

from research import metrics


def _toy_dog(n: int = 400, seed_returns: bool = True) -> pd.DataFrame:
    """Synthetic underdog frame: multiplier 2.5x, alternating wins (40% win rate)."""
    m = np.full(n, 2.5)
    wins = np.arange(n) % 5 < 2  # 40%
    return pd.DataFrame(
        {
            "m_dog": m,
            "breakeven_dog": 1 / m,
            "ev_naive_dog": 0.5 * m - 1,
            "dog_wins": wins,
            "ret_dog": np.where(wins, m - 1, -1.0),
            "total_bnb": np.linspace(5, 50, n),
            "date": pd.date_range("2022-01-01", periods=n, freq="5min"),
            "dog_is_bull": np.ones(n, dtype=bool),
            "bullAmount": np.full(n, 4e18),
            "bearAmount": np.full(n, 6e18),
        }
    )


def test_wilson_ci_centre_and_bounds():
    lo, hi = metrics.wilson_ci(50, 100)
    assert lo < 0.5 < hi
    assert metrics.wilson_ci(0, 100)[0] >= 0.0
    assert metrics.wilson_ci(100, 100)[1] <= 1.0


def test_wilson_ci_empty():
    lo, hi = metrics.wilson_ci(0, 0)
    assert np.isnan(lo) and np.isnan(hi)


def test_backtest_final_odds_math():
    dog = _toy_dog()
    bt = metrics.backtest_final_odds(dog, threshold=0.0)
    # 40% win at 2.5x: mean return = 0.4*1.5 - 0.6 = 0.0
    assert bt["n_bets"] == len(dog)
    assert bt["mean_net_return"] == pytest.approx(0.0)
    assert bt["win_rate"] == pytest.approx(0.4)


def test_backtest_threshold_filters():
    dog = _toy_dog()
    assert metrics.backtest_final_odds(dog, threshold=0.3)["n_bets"] == 0


def test_legacy_rule_selects_more_than_exact_rule():
    # Legacy additive-fee formula overstates EV for multipliers above 2, so at the
    # same nominal threshold it must select at least as many rounds.
    rng = np.random.default_rng(7)
    m = rng.uniform(1.9, 4.0, 3000)
    wins = rng.random(3000) < 1 / m
    dog = pd.DataFrame(
        {
            "m_dog": m,
            "ev_naive_dog": 0.5 * m - 1,
            "dog_wins": wins,
            "ret_dog": np.where(wins, m - 1, -1.0),
            "date": pd.date_range("2022-01-01", periods=3000, freq="5min"),
        }
    )
    exact = metrics.backtest_final_odds(dog, 0.25)["n_bets"]
    legacy = metrics.legacy_rule_backtest(dog, fee=0.03, threshold=0.25)["n_bets"]
    assert legacy >= exact


def test_edge_bin_table_covers_all_rows():
    dog = _toy_dog()
    rows = metrics.edge_bin_table(dog)
    assert sum(r["n"] for r in rows) == len(dog)
    row = next(r for r in rows if r["n"] > 0)
    assert row["breakeven_win_rate"] == pytest.approx(0.4)  # 1/2.5
    assert 0 <= row["win_rate"] <= 1


def test_with_pricing_drops_balanced_and_flags_underdog():
    clean = pd.DataFrame(
        {
            "totalAmount": [10e18, 8e18],
            "bullAmount": [4e18, 4e18],
            "bearAmount": [6e18, 4e18],  # second round exactly balanced
            "up": [True, True],
            "down": [False, False],
            "tie": [False, False],
            "total_bnb": [10.0, 8.0],
            "date": pd.to_datetime(["2022-01-01", "2022-01-02"]),
        }
    )
    dog = metrics.with_pricing(clean, fee=0.03)
    assert len(dog) == 1  # balanced round dropped
    assert bool(dog["dog_is_bull"].iloc[0]) is True
    assert dog["m_dog"].iloc[0] == pytest.approx(0.97 * 10 / 4)
    assert bool(dog["dog_wins"].iloc[0]) is True
