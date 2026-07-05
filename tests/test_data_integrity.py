"""Assertions about the committed dataset that the README's claims depend on."""

import pytest

from research.loaders import DEFAULT_DATA, clean_sample, load_rounds
from research.metrics import fee_stats


@pytest.fixture(scope="module")
def data():
    df = load_rounds(DEFAULT_DATA)
    clean, accounting = clean_sample(df)
    return df, clean, accounting


def test_row_count_and_epochs(data):
    df, _, acc = data
    assert acc["n_rows"] == 144_000
    assert acc["epoch_min"] == 100
    assert acc["epoch_max"] == 144_099
    assert acc["n_missing_epochs"] == 0
    assert acc["n_duplicate_epochs"] == 0
    assert df["epoch"].is_monotonic_increasing


def test_clean_sample_accounting(data):
    _, clean, acc = data
    assert acc["n_clean"] == len(clean)
    assert acc["n_rows"] == acc["n_clean"] + acc["n_voided"] + acc["n_empty_side"]
    assert acc["n_clean"] == 143_856


def test_sample_span(data):
    _, _, acc = data
    assert acc["date_min_utc"].startswith("2021-08-26")
    assert acc["date_max_utc"].startswith("2023-02-06")
    assert acc["median_round_seconds"] == pytest.approx(300, abs=15)


def test_treasury_fee_is_three_percent(data):
    _, clean, _ = data
    fee = fee_stats(clean)
    assert fee["median"] == pytest.approx(0.03, abs=0.001)
