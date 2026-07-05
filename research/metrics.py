"""Statistics behind every number cited in the README.

All functions take the clean sample from :mod:`research.loaders` and return
plain dicts/lists ready for ``results/stats.json``. Conventions:

- The *underdog* is the side with the smaller pool (higher payout multiplier).
- ``m`` is the stake-inclusive payout multiplier ``(1 - fee) * total / side``.
- ``ev_naive`` is the expected net return per unit staked **if** the win
  probability were 0.5: ``0.5 * m - 1`` — the 2021 hypothesis under test.
- A tie (close == lock) loses for both sides; realized returns include ties.
- Returns labelled "at final odds" use the pools measured at lock, an
  infeasible benchmark: no bettor can observe them before committing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

#: Naive-EV bin edges for the README's main table (last bin open-ended).
EDGE_BINS = [-np.inf, 0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, np.inf]
EDGE_LABELS = ["<0", "0–0.1", "0.1–0.25", "0.25–0.5", "0.5–0.75", "0.75–1", "1–1.5", "≥1.5"]


def wilson_ci(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson 95% interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, centre - half), min(1.0, centre + half))


def fee_stats(clean: pd.DataFrame) -> dict:
    """Treasury fee measured from settled rounds: 1 - reward/total."""
    ok = clean[clean["rewardBaseCalAmount"] > 0]
    fee = 1 - ok["rewardAmount"] / ok["totalAmount"]
    return {
        "n_measurable": int(len(ok)),
        "median": float(fee.median()),
        "p01": float(fee.quantile(0.01)),
        "p99": float(fee.quantile(0.99)),
    }


def with_pricing(clean: pd.DataFrame, fee: float) -> pd.DataFrame:
    """Add multiplier/EV/outcome columns for the underdog side of each round.

    Rounds with exactly balanced pools have no underdog and are dropped
    (a handful of rounds; counted by the caller if needed).
    """
    d = clean.copy()
    d["m_bull"] = (1 - fee) * d["totalAmount"] / d["bullAmount"]
    d["m_bear"] = (1 - fee) * d["totalAmount"] / d["bearAmount"]
    dog_is_bull = d["bullAmount"] < d["bearAmount"]
    d = d[d["bullAmount"] != d["bearAmount"]].copy()
    dog_is_bull = dog_is_bull[d.index]
    d["dog_is_bull"] = dog_is_bull
    d["m_dog"] = np.where(dog_is_bull, d["m_bull"], d["m_bear"])
    d["breakeven_dog"] = 1 / d["m_dog"]
    d["ev_naive_dog"] = 0.5 * d["m_dog"] - 1
    d["dog_wins"] = np.where(dog_is_bull, d["up"], d["down"])
    d["ret_dog"] = np.where(d["dog_wins"], d["m_dog"] - 1, -1.0)
    return d


def base_rates(clean: pd.DataFrame) -> dict:
    ret = clean["logret"]
    med_dur = float((clean["closeTimestamp"] - clean["lockTimestamp"]).median())
    per_year = 365.25 * 24 * 3600 / med_dur
    consec = clean.set_index("epoch")["logret"]
    prev = consec.reindex(consec.index - 1)
    mask = prev.notna().values
    ac1 = float(np.corrcoef(consec.values[mask], prev.values[mask])[0, 1])
    return {
        "p_up": float(clean["up"].mean()),
        "n_up": int(clean["up"].sum()),
        "n_down": int(clean["down"].sum()),
        "n_tie": int(clean["tie"].sum()),
        "logret_sd": float(ret.std()),
        "annualized_vol": float(ret.std() * np.sqrt(per_year)),
        "lag1_autocorr": ac1,
        "lag1_autocorr_t": ac1 * float(np.sqrt(mask.sum())),
    }


def edge_bin_table(dog: pd.DataFrame) -> list[dict]:
    """The README's main table: win rate and realized return by implied edge."""
    bins = pd.cut(dog["ev_naive_dog"], EDGE_BINS, right=False, labels=EDGE_LABELS)
    rows = []
    for label, g in dog.groupby(bins, observed=True):
        k, n = int(g["dog_wins"].sum()), len(g)
        lo, hi = wilson_ci(k, n)
        mean_ret = float(g["ret_dog"].mean())
        se = float(g["ret_dog"].std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        rows.append(
            {
                "bin": str(label),
                "n": n,
                "mean_multiplier": float(g["m_dog"].mean()),
                "breakeven_win_rate": float(g["breakeven_dog"].mean()),
                "win_rate": k / n,
                "win_rate_ci": [lo, hi],
                "mean_net_return": mean_ret,
                "return_se": se,
                "return_t": mean_ret / se if se and np.isfinite(se) and se > 0 else None,
            }
        )
    return rows


def calibration(dog: pd.DataFrame, n_bins: int = 20) -> dict:
    """Binned calibration of win frequency on breakeven probability (fig 2).

    One observation per round — the underdog side. The WLS slope answers:
    do final odds price outcomes one-for-one? (1 = perfect calibration,
    0 = the random-walk assumption.)
    """
    d = dog.copy()
    d["bin"] = pd.qcut(d["breakeven_dog"], n_bins, duplicates="drop")
    pts = []
    for _, g in d.groupby("bin", observed=True):
        k, n = int(g["dog_wins"].sum()), len(g)
        lo, hi = wilson_ci(k, n)
        pts.append(
            {
                "breakeven": float(g["breakeven_dog"].mean()),
                "win_rate": k / n,
                "ci": [lo, hi],
                "n": n,
            }
        )
    x = np.array([p["breakeven"] for p in pts])
    y = np.array([p["win_rate"] for p in pts])
    w = np.array([p["n"] for p in pts], dtype=float)
    fit = sm.WLS(y, sm.add_constant(x), weights=w).fit()
    return {
        "points": pts,
        "slope": float(fit.params[1]),
        "slope_se": float(fit.bse[1]),
        "intercept": float(fit.params[0]),
    }


def logit_dog_win(dog: pd.DataFrame) -> dict:
    """P(underdog wins) as a logistic function of its naive implied edge."""
    x = sm.add_constant(dog[["ev_naive_dog"]].astype(float))
    m = sm.Logit(dog["dog_wins"].astype(int), x).fit(disp=0, cov_type="HC1")
    b0, b1 = float(m.params.iloc[0]), float(m.params.iloc[1])
    predict = {v: 1 / (1 + np.exp(-(b0 + b1 * v))) for v in (0, 0.25, 0.5, 1.0, 1.5, 2.0)}
    return {
        "n": int(m.nobs),
        "coef_ev": b1,
        "z_ev": float(m.tvalues.iloc[1]),
        "pseudo_r2": float(m.prsquared),
        "predicted_win_rate_at_ev": {str(k): float(v) for k, v in predict.items()},
    }


def backtest_final_odds(dog: pd.DataFrame, threshold: float) -> dict:
    """Bet 1 unit on the underdog whenever its naive edge clears `threshold`.

    Evaluated at final odds — see the module docstring caveat.
    """
    sel = dog[dog["ev_naive_dog"] >= threshold]
    n = len(sel)
    if n == 0:
        return {"threshold": threshold, "n_bets": 0}
    ret = sel["ret_dog"].to_numpy()
    cum = np.cumsum(ret)
    mean = float(ret.mean())
    se = float(ret.std(ddof=1) / np.sqrt(n))
    # Cluster-robust t by calendar day: rounds are sequential, so also report a
    # t-stat that only assumes independence across days, not across rounds.
    resid = pd.Series(ret - mean, index=sel["date"].dt.floor("D"))
    cluster_var = float((resid.groupby(level=0).sum() ** 2).sum()) / n**2
    return {
        "threshold": threshold,
        "n_bets": n,
        "share_of_rounds": n / len(dog),
        "win_rate": float(sel["dog_wins"].mean()),
        "mean_naive_ev": float(sel["ev_naive_dog"].mean()),
        "mean_net_return": mean,
        "t_stat": mean / se if se > 0 else None,
        "t_stat_cluster_day": mean / np.sqrt(cluster_var) if cluster_var > 0 else None,
        "n_cluster_days": int(resid.index.nunique()),
        "total_pnl_units": float(cum[-1]),
        "max_drawdown_units": float(np.max(np.maximum.accumulate(cum) - cum)),
    }


def legacy_rule_backtest(dog: pd.DataFrame, fee: float, threshold: float = 0.25) -> dict:
    """The 2021 bot's literal rule: ``total/side/2 - (1 + fee) >= threshold``.

    The legacy formula treats the fee as additive, overstating EV for
    multipliers above 2 — so it selects slightly more rounds than the exact
    rule at the same nominal threshold.
    """
    legacy_ev = 0.5 * dog["m_dog"] / (1 - fee) - (1 + fee)
    sel = dog[legacy_ev >= threshold]
    ret = sel["ret_dog"].to_numpy()
    n = len(sel)
    se = float(ret.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    return {
        "threshold": threshold,
        "n_bets": n,
        "win_rate": float(sel["dog_wins"].mean()),
        "mean_net_return": float(ret.mean()),
        "t_stat": float(ret.mean() / se) if se and np.isfinite(se) and se > 0 else None,
        "mean_legacy_quoted_ev": float(legacy_ev[legacy_ev >= threshold].mean()),
    }


def quarterly_returns(dog: pd.DataFrame, threshold: float = 0.25) -> list[dict]:
    """Mean underdog return at final odds by calendar quarter (fig 4).

    Quarters are keyed by the round's lock timestamp. ``median_pool_bnb`` is
    the median total pool of the *selected* bets — the depth the premium had
    to live in that quarter.
    """
    sel = dog[dog["ev_naive_dog"] >= threshold].copy()
    sel["quarter"] = sel["date"].dt.to_period("Q").astype(str)
    rows = []
    for q, g in sel.groupby("quarter"):
        ret = g["ret_dog"].to_numpy()
        n = len(ret)
        se = float(ret.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        rows.append(
            {
                "quarter": q,
                "n_bets": n,
                "win_rate": float(g["dog_wins"].mean()),
                "mean_net_return": float(ret.mean()),
                "se": se,
                "median_pool_bnb": float(g["total_bnb"].median()),
            }
        )
    return rows


def pool_size_gradient(dog: pd.DataFrame, threshold: float = 0.25) -> list[dict]:
    """Underdog returns at final odds by total-pool-size quartile."""
    sel = dog[dog["ev_naive_dog"] >= threshold].copy()
    quartile = pd.qcut(sel["total_bnb"], 4, labels=["Q1 smallest", "Q2", "Q3", "Q4 largest"])
    rows = []
    for q, g in sel.groupby(quartile, observed=True):
        ret = g["ret_dog"].to_numpy()
        n = len(ret)
        se = float(ret.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        rows.append(
            {
                "quartile": str(q),
                "median_pool_bnb": float(g["total_bnb"].median()),
                "n_bets": n,
                "mean_net_return": float(ret.mean()),
                "t_stat": float(ret.mean() / se) if se and se > 0 else None,
            }
        )
    return rows


def dilution_effect(dog: pd.DataFrame, fee: float, stake_bnb: float, threshold: float) -> dict:
    """Backtest mean return after adding your own stake to the underdog pool."""
    sel = dog[dog["ev_naive_dog"] >= threshold]
    side_bnb = np.where(sel["dog_is_bull"], sel["bullAmount"], sel["bearAmount"]) / 1e18
    m_diluted = (1 - fee) * (sel["total_bnb"] + stake_bnb) / (side_bnb + stake_bnb)
    ret = np.where(sel["dog_wins"], m_diluted - 1, -1.0)
    return {
        "stake_bnb": stake_bnb,
        "threshold": threshold,
        "mean_net_return": float(ret.mean()),
    }


def crowd_information(clean: pd.DataFrame) -> dict:
    """Does the final pool share predict direction beyond last-round momentum?"""
    c = clean.set_index("epoch")
    prev = c["logret"].reindex(c.index - 1)
    d = c.assign(r_prev_pct=prev.values * 100).dropna(subset=["r_prev_pct"]).copy()
    d["bull_share"] = d["bullAmount"] / d["totalAmount"]
    y = d["up"].astype(int)

    def fit(cols: list[str]) -> dict:
        m = sm.Logit(y, sm.add_constant(d[cols].astype(float))).fit(disp=0, cov_type="HC1")
        return {
            "coef": {k: float(v) for k, v in m.params.items()},
            "z": {k: float(v) for k, v in m.tvalues.items()},
            "pseudo_r2": float(m.prsquared),
        }

    corr = float(np.corrcoef(d["bull_share"], d["r_prev_pct"])[0, 1])
    return {
        "n": int(len(d)),
        "momentum_only": fit(["r_prev_pct"]),
        "imbalance_only": fit(["bull_share"]),
        "both": fit(["bull_share", "r_prev_pct"]),
        "corr_share_vs_prev_return": corr,
    }


def outage_gaps(df: pd.DataFrame, min_hours: float = 1.0) -> list[dict]:
    """Gaps between consecutive rounds (chain halts, contract pauses)."""
    d = df.sort_values("epoch")
    gap_s = d["startTimestamp"].diff()
    hit = d[gap_s > min_hours * 3600]
    return [
        {
            "epoch": int(r.epoch),
            "date_utc": str(pd.to_datetime(r.startTimestamp, unit="s")),
            "gap_hours": round(float(g) / 3600, 1),
        }
        for r, g in zip(hit.itertuples(), gap_s[hit.index], strict=True)
    ]
