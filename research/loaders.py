"""Load and filter the round-history dataset (see data/README.md for the schema)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = REPO_ROOT / "data" / "rounds.csv.gz"

_WEI = 1e18
_PRICE_SCALE = 1e8


def load_rounds(path: str | Path = DEFAULT_DATA) -> pd.DataFrame:
    """Raw dataset with derived outcome/price columns, one row per round."""
    df = pd.read_csv(path)
    # The CSV stores TRUE/FALSE strings; be robust to either bool or str parsing.
    df["oracleCalled"] = df["oracleCalled"].astype(str).str.upper().eq("TRUE")
    df["up"] = df["closePrice"] > df["lockPrice"]
    df["down"] = df["closePrice"] < df["lockPrice"]
    df["tie"] = df["closePrice"] == df["lockPrice"]
    df["total_bnb"] = df["totalAmount"] / _WEI
    df["date"] = pd.to_datetime(df["lockTimestamp"], unit="s")
    return df


def clean_sample(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Analysis sample: settled normally, both pools funded.

    Returns the filtered frame plus the exclusion accounting used in the README.
    """
    settled = df["oracleCalled"]
    funded = (df["bullAmount"] > 0) & (df["bearAmount"] > 0)
    clean = df[settled & funded].copy()
    with np.errstate(divide="ignore"):
        clean["logret"] = np.log(clean["closePrice"] / clean["lockPrice"])
    accounting = {
        "n_rows": int(len(df)),
        "n_voided": int((~settled).sum()),
        "n_empty_side": int((settled & ~funded).sum()),
        "n_clean": int(len(clean)),
        "n_ties": int(clean["tie"].sum()),
        "epoch_min": int(df["epoch"].min()),
        "epoch_max": int(df["epoch"].max()),
        "n_missing_epochs": int(
            df["epoch"].max() - df["epoch"].min() + 1 - df["epoch"].nunique()
        ),
        "n_duplicate_epochs": int(df["epoch"].duplicated().sum()),
        "date_min_utc": str(pd.to_datetime(df["startTimestamp"].min(), unit="s")),
        "date_max_utc": str(pd.to_datetime(df["closeTimestamp"].max(), unit="s")),
        "median_round_seconds": float((df["closeTimestamp"] - df["lockTimestamp"]).median()),
        "median_pool_bnb": float(clean["total_bnb"].median()),
    }
    return clean, accounting
