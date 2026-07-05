"""Regenerate every statistic and figure cited in the README.

    python -m research.pipeline

Reads data/rounds.csv.gz, writes results/stats.json + results/edge_bins.md
and figures/fig1..fig4 (png + svg). Deterministic; runs in ~30s on a laptop.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from research import figures, metrics
from research.loaders import DEFAULT_DATA, REPO_ROOT, clean_sample, load_rounds

BOT_THRESHOLD = 0.25  # the 2021 bot's live EV threshold


def build_stats(data_path: Path) -> tuple[dict, object]:
    df = load_rounds(data_path)
    clean, accounting = clean_sample(df)
    fee = metrics.fee_stats(clean)
    dog = metrics.with_pricing(clean, fee["median"])

    stats = {
        "dataset": accounting,
        "fee": fee,
        "base_rates": metrics.base_rates(clean),
        "underdog_overall": {
            "n": int(len(dog)),
            "win_rate": float(dog["dog_wins"].mean()),
            "mean_naive_ev": float(dog["ev_naive_dog"].mean()),
            "share_naive_ev_ge_10pct": float((dog["ev_naive_dog"] >= 0.10).mean()),
            "median_multiplier": float(dog["m_dog"].median()),
            "mean_net_return": float(dog["ret_dog"].mean()),
        },
        "edge_bins": metrics.edge_bin_table(dog),
        "calibration": metrics.calibration(dog),
        "logit": metrics.logit_dog_win(dog),
        "backtest_final_odds": {
            "note": (
                "Idealized benchmark at FINAL odds (pools at lock). Infeasible live: "
                "bets commit before lock, after which odds keep moving; own-bet "
                "dilution and gas excluded except where stated."
            ),
            "grid": [
                metrics.backtest_final_odds(dog, t)
                for t in (0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.5, 1.0)
            ],
            "legacy_2021_rule": metrics.legacy_rule_backtest(dog, fee["median"], BOT_THRESHOLD),
            "dilution_0p1bnb": metrics.dilution_effect(dog, fee["median"], 0.1, BOT_THRESHOLD),
            "dilution_1bnb": metrics.dilution_effect(dog, fee["median"], 1.0, BOT_THRESHOLD),
        },
        "by_quarter_tau25": metrics.quarterly_returns(dog, BOT_THRESHOLD),
        "by_pool_size_tau25": metrics.pool_size_gradient(dog, BOT_THRESHOLD),
        "crowd": metrics.crowd_information(clean),
        "outages_over_1h": metrics.outage_gaps(df),
    }
    return stats, dog


def _num(s: str) -> str:
    """Typographic minus for negative numbers, matching the README's tables."""
    return s.replace("-", "−")


def edge_bins_markdown(stats: dict) -> str:
    lines = [
        "| Implied edge (naive EV) | Rounds | Mean payout | Breakeven win rate "
        "| Actual win rate | Realized return/bet | t |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in stats["edge_bins"]:
        t = _num(f"{r['return_t']:+.1f}") if r["return_t"] is not None else "—"
        ret = _num(f"{r['mean_net_return']:+.2%}")
        lines.append(
            f"| {r['bin']} | {r['n']:,} | {r['mean_multiplier']:.2f}× "
            f"| {r['breakeven_win_rate']:.1%} | {r['win_rate']:.1%} "
            f"| {ret} | {t} |"
        )
    u = stats["underdog_overall"]
    all_ret = _num(f"{u['mean_net_return']:+.2%}")
    lines.append(
        f"| **all** | {u['n']:,} | {2 * (1 + u['mean_naive_ev']):.2f}× | — "
        f"| {u['win_rate']:.1%} | {all_ret} | — |"
    )
    lines.append("")
    lines.append(
        "*Realized returns are computed at final odds — an infeasible benchmark: "
        "they condition on the closing pool, which no bettor can observe before committing.*"
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--results-dir", type=Path, default=REPO_ROOT / "results")
    parser.add_argument("--figures-dir", type=Path, default=REPO_ROOT / "figures")
    args = parser.parse_args()

    stats, dog = build_stats(args.data)

    args.results_dir.mkdir(parents=True, exist_ok=True)
    with open(args.results_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=1, default=float)
    (args.results_dir / "edge_bins.md").write_text(edge_bins_markdown(stats), encoding="utf-8")

    fee = stats["fee"]["median"]
    footnote = figures.make_footnote(stats["dataset"])
    figures.fig1_implied_edge(dog, args.figures_dir, BOT_THRESHOLD, footnote)
    figures.fig2_calibration(stats["calibration"], args.figures_dir, footnote)
    figures.fig3_return_by_edge(stats["edge_bins"], fee, args.figures_dir, footnote)
    figures.fig4_decay(stats["by_quarter_tau25"], fee, args.figures_dir, footnote)

    u, bt = stats["underdog_overall"], stats["backtest_final_odds"]
    t25 = next(g for g in bt["grid"] if g["threshold"] == BOT_THRESHOLD)
    print(f"clean sample          {stats['dataset']['n_clean']:,} rounds")
    print(f"treasury fee          {fee:.2%}")
    print(f"mean naive edge       {u['mean_naive_ev']:+.1%} (the illusion)")
    print(f"underdog win rate     {u['win_rate']:.1%} (vs 50% assumed)")
    print(
        f"tau>=25% at final odds {t25['mean_net_return']:+.2%}/bet "
        f"(t={t25['t_stat']:.1f}, n={t25['n_bets']:,}) - infeasible benchmark"
    )
    print(f"calibration slope     {stats['calibration']['slope']:.3f}")
    print(f"wrote {args.results_dir / 'stats.json'} and 4 figures -> {args.figures_dir}")


if __name__ == "__main__":
    main()
