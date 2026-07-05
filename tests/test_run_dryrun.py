"""Dry-run safety: inside the betting window the loop must not send anything."""

from dataclasses import dataclass

import pytest

from bot.config import Config
from bot.run import BET_WINDOW_SECONDS, run_once


@dataclass
class _StubRound:
    epoch: int = 42
    lock_ts: int = 1_000_000
    close_ts: int = 1_000_300
    total: float = 10.0
    bull: float = 2.0  # underdog: multiplier 0.97*10/2 = 4.85, naive EV +1.43
    bear: float = 8.0


class _StubClient:
    def __init__(self, seconds_to_lock: int):
        self._now = _StubRound().lock_ts - seconds_to_lock
        self.bets_sent: list = []

    def current_epoch(self) -> int:
        return 42

    def get_round(self, epoch: int) -> _StubRound:
        return _StubRound()

    def chain_time(self) -> int:
        return self._now

    def bet(self, side, epoch, amount):  # would be a real transaction
        self.bets_sent.append((side, epoch, amount))
        return "0xdead"


def _cfg(dry_run: bool) -> Config:
    return Config(
        rpc_url="http://unused",
        wallet_address="0x0" if not dry_run else "",
        private_key="0x0" if not dry_run else "",
        bet_amount_bnb=0.05,
        ev_threshold=0.25,
        claim_lookback=10,
        dry_run=dry_run,
    )


def test_dry_run_never_sends_inside_window():
    client = _StubClient(seconds_to_lock=8)  # inside the 10s window
    sleep_s = run_once(client, _cfg(dry_run=True), fee=0.03, handled=set())
    assert client.bets_sent == []
    assert sleep_s == pytest.approx(260.0)  # round handled, skip to the next


def test_live_mode_would_send(monkeypatch):
    client = _StubClient(seconds_to_lock=8)
    cfg = _cfg(dry_run=False)
    monkeypatch.setattr("bot.run._sweep_claims", lambda *a, **k: None)
    run_once(client, cfg, fee=0.03, handled=set())
    assert client.bets_sent == [("bull", 42, 0.05)]


def test_never_bets_same_epoch_twice(monkeypatch):
    # Regression: a claim-sweep failure after the bet must not re-trigger the
    # bet path when the loop retries inside the same window.
    client = _StubClient(seconds_to_lock=8)
    cfg = _cfg(dry_run=False)

    def _boom(*a, **k):
        raise ConnectionError("rpc died mid-sweep")

    monkeypatch.setattr("bot.run._sweep_claims", _boom)
    handled: set[int] = set()
    run_once(client, cfg, fee=0.03, handled=handled)  # sweep failure is swallowed
    run_once(client, cfg, fee=0.03, handled=handled)  # retry in the same window
    assert client.bets_sent == [("bull", 42, 0.05)]  # exactly one bet


def test_outside_window_sleeps_toward_lock():
    client = _StubClient(seconds_to_lock=120)
    sleep_s = run_once(client, _cfg(dry_run=True), fee=0.03, handled=set())
    assert client.bets_sent == []
    # wakes up just inside the betting window
    assert 100 < sleep_s <= 120 - BET_WINDOW_SECONDS + 3


def test_after_lock_waits_for_next_round():
    client = _StubClient(seconds_to_lock=-30)
    assert run_once(client, _cfg(dry_run=True), fee=0.03, handled=set()) == pytest.approx(5.0)
