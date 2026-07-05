"""The four README figures. Style: quiet chrome, direct labels, takeaway titles.

Colors follow a colorblind-validated palette: blue carries the data, one warm
accent marks the naive hypothesis, references and chrome stay gray.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

BLUE = "#2a78d6"
BLUE_DARK = "#1c5cab"
ACCENT = "#eb6834"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"

#: Fallback provenance line; the pipeline passes one derived from the actual sample.
FOOTNOTE = "143,856 settled rounds · PancakePredictionV2 (BNB/USD) · Aug 2021 – Feb 2023"


def make_footnote(accounting: dict) -> str:
    """Provenance line derived from the sample actually analyzed."""
    start = accounting["date_min_utc"][:7]
    end = accounting["date_max_utc"][:7]
    return (
        f"{accounting['n_clean']:,} settled rounds · PancakePredictionV2 (BNB/USD) "
        f"· {start} – {end}"
    )


def _new_fig(
    title: str, subtitle: str, figsize: tuple[float, float] = (8.6, 5.2), wrap: int = 108
) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelcolor=INK_2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    fig.suptitle(title, x=0.06, y=0.972, ha="left", fontsize=13.5, fontweight="bold", color=INK)
    ax.set_title(
        textwrap.fill(subtitle, wrap), loc="left", fontsize=9.3, color=INK_2, pad=12
    )
    return fig, ax


def _finish(fig: plt.Figure, out_dir: Path, name: str, footnote: str = FOOTNOTE) -> None:
    fig.text(0.06, 0.015, footnote, fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0.01, 0.045, 0.99, 0.90))
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", facecolor="white")
    fig.savefig(out_dir / f"{name}.svg", facecolor="white")
    plt.close(fig)


def fig1_implied_edge(
    dog: pd.DataFrame, out_dir: Path, threshold: float = 0.25, footnote: str = FOOTNOTE
) -> None:
    """Histogram of the naive implied underdog edge."""
    ev = dog["ev_naive_dog"].clip(upper=1.5)
    share_pos10 = float((dog["ev_naive_dog"] >= 0.10).mean())
    mean_ev = float(dog["ev_naive_dog"].mean())

    fig, ax = _new_fig(
        "The edge that wasn't",
        "Implied net return per 1 BNB on the underdog side if every round were a coin flip "
        "(EV = 0.5·m − 1 at final odds). Values above +150% are folded into the last bar.",
    )
    ax.hist(ev, bins=64, range=(-0.10, 1.50), color=BLUE, edgecolor="white", linewidth=0.3)
    ax.axvline(0, color=MUTED, linewidth=1.0, linestyle="--")
    ax.axvline(threshold, color=ACCENT, linewidth=1.2, linestyle="--")
    ymax = ax.get_ylim()[1]
    ax.text(
        threshold + 0.015, ymax * 0.88,
        "the 2021 bot's live threshold (+25%)", color=ACCENT, fontsize=8.8, ha="left",
    )
    ax.annotate(
        f"mean +{mean_ev:.0%} — and {share_pos10:.0%} of rounds imply ≥ +10%",
        xy=(mean_ev, ymax * 0.45), xytext=(0.42, ymax * 0.60),
        color=INK, fontsize=9.5,
        arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8},
    )
    ax.set_xlabel(
        "implied edge under the 50/50 assumption (+0% = breakeven)", fontsize=9.5, color=INK_2
    )
    ax.set_ylabel("rounds", fontsize=9.5, color=INK_2)
    ticks = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.4875]
    ax.set_xticks(ticks, [f"{t:+.0%}" for t in ticks[:-1]] + ["≥+150%"])
    _finish(fig, out_dir, "fig1_implied_edge_dist", footnote)


def fig2_calibration(cal: dict, out_dir: Path, footnote: str = FOOTNOTE) -> None:
    """Hero figure: binned win frequency vs breakeven probability."""
    pts = cal["points"]
    x = np.array([p["breakeven"] for p in pts])
    y = np.array([p["win_rate"] for p in pts])
    lo = np.array([p["ci"][0] for p in pts])
    hi = np.array([p["ci"][1] for p in pts])
    n = np.array([p["n"] for p in pts], dtype=float)

    fig, ax = _new_fig(
        "The odds are prices",
        "Each dot is one twentieth of rounds (underdog side): how often it won vs the "
        "win rate its final odds require to break even. Dot area ∝ rounds.",
        figsize=(7.2, 6.7),
        wrap=88,
    )
    axmin = float(min(x.min(), y.min()) - 0.035)
    axmax = 0.56
    ax.plot([axmin, axmax], [axmin, axmax], color=MUTED, linewidth=1.0, linestyle="--", zorder=1)
    ax.axhline(0.5, color=ACCENT, linewidth=1.2, linestyle="--", zorder=1)
    xs = np.linspace(axmin, axmax, 2)
    ax.plot(xs, cal["intercept"] + cal["slope"] * xs, color=BLUE_DARK, linewidth=1.6, zorder=2)
    ax.errorbar(x, y, yerr=[y - lo, hi - y], fmt="none", ecolor=BLUE, elinewidth=0.9, zorder=3)
    ax.scatter(
        x, y, s=18 + 140 * n / n.max(), color=BLUE, edgecolor="white", linewidth=0.6, zorder=4
    )

    ax.text(
        axmin + 0.008, 0.506,
        "random-walk assumption:\nevery side wins 50% (the 2021 hypothesis)",
        color=ACCENT, fontsize=8.8, ha="left", va="bottom", linespacing=1.4,
    )
    ax.text(
        0.363, 0.352, "perfectly calibrated odds",
        color=MUTED, fontsize=8.8, ha="center", va="top", rotation=45,
        rotation_mode="anchor",
    )
    ax.text(
        0.345, 0.265,
        f"fitted slope {cal['slope']:.2f} (SE {cal['slope_se']:.2f}):\n"
        "steep, nearly one-for-one — but longshots\nrun slightly above the diagonal",
        color=BLUE_DARK, fontsize=9, ha="left",
    )
    ax.set_xlabel(
        "breakeven win rate implied by final odds  (= 1 / payout multiplier)",
        fontsize=9.5, color=INK_2,
    )
    ax.set_ylabel("empirical win rate", fontsize=9.5, color=INK_2)
    ax.set_xlim(axmin, axmax)
    ax.set_ylim(axmin, axmax)
    ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    _finish(fig, out_dir, "fig2_calibration", footnote)


def fig3_return_by_edge(
    bin_rows: list[dict], fee: float, out_dir: Path, footnote: str = FOOTNOTE
) -> None:
    """Dot-and-whisker: realized net return per bin of implied edge."""
    rows = [r for r in bin_rows if r["n"] > 0]
    xs = np.arange(len(rows))
    y = np.array([r["mean_net_return"] for r in rows])
    se = np.array([r["return_se"] for r in rows], dtype=float)
    err = np.where(np.isfinite(se), 1.959964 * se, 0.0)  # single-round bins get no whisker

    fig, ax = _new_fig(
        "Returns collapse toward minus the fee — except in the far tail",
        "Mean realized net return per 1 BNB staked on the underdog at final odds, by "
        "implied-edge bin; whiskers 95% CI. Final odds are an infeasible benchmark: they "
        "condition on the closing pool, which no bettor can observe before committing.",
    )
    ax.axhline(0, color=MUTED, linewidth=1.0, linestyle="--")
    ax.axhline(-fee, color=ACCENT, linewidth=1.1, linestyle="--")
    ax.errorbar(xs, y, yerr=err, fmt="none", ecolor=BLUE, elinewidth=1.4, capsize=3)
    ax.scatter(xs, y, s=46, color=BLUE, edgecolor="white", linewidth=0.8, zorder=4)
    for i, r in enumerate(rows):
        ax.annotate(
            f"{r['mean_net_return']:+.1%}", (i, y[i]),
            textcoords="offset points", xytext=(9, 4), fontsize=8.3, color=BLUE_DARK,
        )
    ax.text(
        len(rows) - 0.45, 0.012, "breakeven", color=MUTED, fontsize=8.5, ha="right", va="bottom"
    )
    ax.text(
        len(rows) - 0.45, -fee - 0.014, f"treasury fee (−{fee:.0%})",
        color=ACCENT, fontsize=8.5, ha="right", va="top",
    )
    ax.set_xticks(xs, [r["bin"] for r in rows])
    ax.set_xlabel(
        "implied edge bin (naive EV under the 50/50 assumption)", fontsize=9.5, color=INK_2
    )
    ax.set_ylabel("mean net return per bet", fontsize=9.5, color=INK_2)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:+.0%}")
    _finish(fig, out_dir, "fig3_return_by_edge_bin", footnote)


def fig4_decay(
    quarters: list[dict], fee: float, out_dir: Path, footnote: str = FOOTNOTE
) -> None:
    """The residual anomaly by calendar quarter, tracking pool depth."""
    rows = [q for q in quarters if q["n_bets"] >= 200]
    xs = np.arange(len(rows))
    y = np.array([q["mean_net_return"] for q in rows])
    band = 1.959964 * np.array([q["se"] for q in rows])

    fig, ax = _new_fig(
        "The residual premium faded by 2022, returning only in thin pools",
        "Mean net return per 1 BNB on underdogs with implied edge ≥ +25%, at final odds, by "
        "quarter; band 95% CI. Same infeasible-benchmark caveat as figure 3.",
    )
    ax.axhline(0, color=MUTED, linewidth=1.0, linestyle="--")
    ax.axhline(-fee, color=ACCENT, linewidth=1.1, linestyle="--")
    ax.fill_between(xs, y - band, y + band, color=BLUE, alpha=0.16, linewidth=0)
    ax.plot(
        xs, y, color=BLUE, linewidth=2.0, marker="o", markersize=5.5,
        markeredgecolor="white", markeredgewidth=0.8,
    )
    for i, q in enumerate(rows):
        va, dy = ("bottom", 8) if i % 2 == 0 else ("top", -10)
        ax.annotate(
            f"{q['mean_net_return']:+.0%}", (i, y[i]), textcoords="offset points",
            xytext=(0, dy), ha="center", va=va, fontsize=8.5, color=BLUE_DARK,
        )
    ax.text(
        len(rows) - 0.5, -fee - 0.012, f"treasury fee (−{fee:.0%})",
        color=ACCENT, fontsize=8.5, ha="right", va="top",
    )
    labels = [f"{q['quarter']}\n{q['median_pool_bnb']:.0f} BNB" for q in rows]
    ax.set_xticks(xs, labels)
    ax.set_xlabel(
        "calendar quarter · median pool of selected bets", fontsize=9.5, color=INK_2
    )
    ax.set_ylabel("mean net return per bet", fontsize=9.5, color=INK_2)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:+.0%}")
    _finish(fig, out_dir, "fig4_decay_by_quarter", footnote)
