import pytest

from bot.config import load_config


def _base_env(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("BET_AMOUNT_BNB", "0.05")
    monkeypatch.setenv("EV_THRESHOLD", "0.25")
    monkeypatch.setenv("CLAIM_LOOKBACK", "50")


def test_defaults_are_safe(monkeypatch):
    _base_env(monkeypatch)
    cfg = load_config()
    assert cfg.dry_run is True
    assert cfg.ev_threshold == 0.25


def test_negative_threshold_rejected(monkeypatch):
    # EV_THRESHOLD=-0.1 would make the bot bet negative-EV rounds (even
    # perfectly balanced pools quote EV = -fee > -0.1).
    _base_env(monkeypatch)
    monkeypatch.setenv("EV_THRESHOLD", "-0.1")
    with pytest.raises(ValueError, match="EV_THRESHOLD"):
        load_config()


def test_zero_lookback_rejected(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.setenv("CLAIM_LOOKBACK", "0")
    with pytest.raises(ValueError, match="CLAIM_LOOKBACK"):
        load_config()


def test_live_requires_credentials(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.delenv("WALLET_ADDRESS", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    with pytest.raises(ValueError, match="WALLET_ADDRESS"):
        load_config()
