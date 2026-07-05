"""End-to-end pipeline smoke test on a 1,000-round fixture."""

import json
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "rounds_sample.csv"


def test_pipeline_runs_and_writes_outputs(tmp_path):
    results = tmp_path / "results"
    figs = tmp_path / "figures"
    proc = subprocess.run(
        [
            sys.executable, "-m", "research.pipeline",
            "--data", str(FIXTURE),
            "--results-dir", str(results),
            "--figures-dir", str(figs),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[1],
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr

    stats = json.loads((results / "stats.json").read_text())
    assert stats["dataset"]["n_clean"] >= 900
    assert 0.02 <= stats["fee"]["median"] <= 0.04
    assert 0.3 <= stats["underdog_overall"]["win_rate"] <= 0.5
    assert (results / "edge_bins.md").read_text(encoding="utf-8").count("|") > 20
    for name in (
        "fig1_implied_edge_dist",
        "fig2_calibration",
        "fig3_return_by_edge_bin",
        "fig4_decay_by_quarter",
    ):
        assert (figs / f"{name}.png").stat().st_size > 10_000
