"""Thin web3 client for the PancakePredictionV2 contract on BNB Chain."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from bot.config import Config

#: PancakeSwap Prediction V2 (BNB/USD) — https://bscscan.com/address/0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA
PREDICTION_ADDRESS = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"
_ABI_PATH = Path(__file__).parent / "abi" / "prediction_v2.json"

# Field offsets of the contract's `rounds()` struct.
_LOCK_TS, _CLOSE_TS = 2, 3
_TOTAL, _BULL, _BEAR = 8, 9, 10

_WEI = 10**18


@dataclass(frozen=True)
class Round:
    epoch: int
    lock_ts: int
    close_ts: int
    total: float  # BNB
    bull: float
    bear: float


class PredictionClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.w3 = Web3(Web3.HTTPProvider(cfg.rpc_url, request_kwargs={"timeout": 15}))
        # BNB Chain blocks carry validator extraData that the default client rejects.
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(PREDICTION_ADDRESS),
            abi=json.loads(_ABI_PATH.read_text()),
        )

    # ---- reads -----------------------------------------------------------

    def treasury_fee(self) -> float:
        """Current fee as a fraction (contract stores basis points / 10000)."""
        return self.contract.functions.treasuryFee().call() / 10_000

    def current_epoch(self) -> int:
        return self.contract.functions.currentEpoch().call()

    def get_round(self, epoch: int) -> Round:
        r = self.contract.functions.rounds(epoch).call()
        return Round(
            epoch=epoch,
            lock_ts=r[_LOCK_TS],
            close_ts=r[_CLOSE_TS],
            total=r[_TOTAL] / _WEI,
            bull=r[_BULL] / _WEI,
            bear=r[_BEAR] / _WEI,
        )

    def chain_time(self) -> int:
        return self.w3.eth.get_block("latest")["timestamp"]

    def balance_bnb(self) -> float:
        account = Web3.to_checksum_address(self.cfg.wallet_address)
        return self.w3.eth.get_balance(account) / _WEI

    def claimable_epochs(self, lookback: int) -> list[int]:
        """Epochs with unclaimed winnings among the wallet's last `lookback` bets.

        Uses `getUserRounds` pagination (bets only) instead of scanning every
        epoch, then confirms with `claimable` — a handful of calls instead of
        one per historical round.
        """
        account = Web3.to_checksum_address(self.cfg.wallet_address)
        n = self.contract.functions.getUserRoundsLength(account).call()
        if n == 0:
            return []
        cursor = max(0, n - lookback)
        epochs, bets, _ = self.contract.functions.getUserRounds(
            account, cursor, lookback
        ).call()
        unclaimed = [e for e, (_, _, claimed) in zip(epochs, bets, strict=True) if not claimed]
        return [
            e
            for e in unclaimed
            if self.contract.functions.claimable(e, account).call()
        ]

    # ---- transactions ----------------------------------------------------

    def _send(self, fn, value_wei: int = 0, gas: int = 250_000) -> str:
        account = Web3.to_checksum_address(self.cfg.wallet_address)
        tx = fn.build_transaction(
            {
                "chainId": 56,
                "from": account,
                "gas": gas,
                "gasPrice": max(self.w3.eth.gas_price, Web3.to_wei(1, "gwei")),
                "nonce": self.w3.eth.get_transaction_count(account, "pending"),
                "value": value_wei,
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, self.cfg.private_key)
        return self.w3.eth.send_raw_transaction(signed.raw_transaction).hex()

    def bet(self, side: str, epoch: int, amount_bnb: float) -> str:
        if side not in ("bull", "bear"):
            raise ValueError(f"side must be 'bull' or 'bear', got {side!r}")
        fn = (
            self.contract.functions.betBull(epoch)
            if side == "bull"
            else self.contract.functions.betBear(epoch)
        )
        return self._send(fn, value_wei=Web3.to_wei(amount_bnb, "ether"))

    def claim(self, epochs: list[int]) -> str:
        fn = self.contract.functions.claim(epochs)
        return self._send(fn, gas=150_000 + 100_000 * len(epochs))
