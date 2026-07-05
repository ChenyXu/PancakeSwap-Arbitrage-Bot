"""Client-layer checks that need no network: ABI offsets and claim pagination."""

import json
from pathlib import Path

import pytest

from bot import client as client_mod
from bot.client import PredictionClient

ABI = json.loads((Path(__file__).parents[1] / "bot" / "abi" / "prediction_v2.json").read_text())


def test_rounds_struct_offsets_match_abi():
    rounds = next(e for e in ABI if e.get("type") == "function" and e.get("name") == "rounds")
    names = [o["name"] for o in rounds["outputs"]]
    assert names[client_mod._LOCK_TS] == "lockTimestamp"
    assert names[client_mod._CLOSE_TS] == "closeTimestamp"
    assert names[client_mod._TOTAL] == "totalAmount"
    assert names[client_mod._BULL] == "bullAmount"
    assert names[client_mod._BEAR] == "bearAmount"


class _Call:
    def __init__(self, value):
        self._value = value

    def call(self):
        return self._value


class _FakeFunctions:
    """Mimics contract.functions for the getUserRounds pagination path."""

    def __init__(self, epochs, bets, claimable_epochs):
        self._epochs = epochs
        self._bets = bets  # list of (position, amount, claimed)
        self._claimable = claimable_epochs

    def getUserRoundsLength(self, account):
        return _Call(len(self._epochs))

    def getUserRounds(self, account, cursor, size):
        return _Call(
            (self._epochs[cursor : cursor + size], self._bets[cursor : cursor + size], 0)
        )

    def claimable(self, epoch, account):
        return _Call(epoch in self._claimable)


def _client_with(epochs, bets, claimable):
    c = PredictionClient.__new__(PredictionClient)  # skip network __init__
    c.cfg = type("Cfg", (), {"wallet_address": "0x" + "1" * 40})()
    c.contract = type("Contract", (), {"functions": _FakeFunctions(epochs, bets, claimable)})()
    return c


def test_claimable_epochs_filters_claimed_and_losses():
    epochs = [10, 11, 12, 13]
    bets = [(0, 1, True), (1, 1, False), (0, 1, False), (1, 1, False)]
    # 11 lost (not claimable), 12 won and unclaimed, 13 won and unclaimed
    c = _client_with(epochs, bets, claimable={12, 13})
    assert c.claimable_epochs(lookback=10) == [12, 13]


def test_claimable_epochs_lookback_window():
    epochs = list(range(100, 160))
    bets = [(0, 1, False)] * 60
    c = _client_with(epochs, bets, claimable=set(epochs))
    got = c.claimable_epochs(lookback=15)
    assert got == list(range(145, 160))  # only the last 15 bets are scanned


def test_claimable_epochs_no_bets():
    c = _client_with([], [], claimable=set())
    assert c.claimable_epochs(lookback=15) == []


def test_bet_rejects_unknown_side():
    c = PredictionClient.__new__(PredictionClient)
    with pytest.raises(ValueError):
        c.bet("up", 1, 0.1)
