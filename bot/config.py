"""Environment-based configuration. Copy .env.example to .env and fill it in."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    rpc_url: str
    wallet_address: str
    private_key: str
    bet_amount_bnb: float
    ev_threshold: float
    claim_lookback: int
    dry_run: bool


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> Config:
    """Read configuration from the environment (and a local .env, if present).

    In dry-run mode the wallet address and private key may be left empty:
    no transaction is ever signed or sent.
    """
    load_dotenv()
    dry_run = _as_bool(os.getenv("DRY_RUN", "true"))
    cfg = Config(
        rpc_url=os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/"),
        wallet_address=os.getenv("WALLET_ADDRESS", ""),
        private_key=os.getenv("PRIVATE_KEY", ""),
        bet_amount_bnb=float(os.getenv("BET_AMOUNT_BNB", "0.01")),
        ev_threshold=float(os.getenv("EV_THRESHOLD", "0.25")),
        claim_lookback=int(os.getenv("CLAIM_LOOKBACK", "100")),
        dry_run=dry_run,
    )
    if not cfg.dry_run and (not cfg.wallet_address or not cfg.private_key):
        raise ValueError("WALLET_ADDRESS and PRIVATE_KEY are required unless DRY_RUN=true")
    if cfg.bet_amount_bnb <= 0:
        raise ValueError("BET_AMOUNT_BNB must be positive")
    if cfg.ev_threshold < 0:
        # A negative threshold accepts negative-EV bets — e.g. every balanced round.
        raise ValueError("EV_THRESHOLD must be >= 0")
    if cfg.claim_lookback < 1:
        raise ValueError("CLAIM_LOOKBACK must be >= 1")
    return cfg
