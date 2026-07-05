"""Bot entry point: ``python -m bot.run`` (add ``--live`` to send real transactions).

Once per round, in the last seconds before lock, the bot compares both sides'
expected value at the quoted odds and bets the side clearing the configured
threshold — then sweeps any unclaimed winnings. Between rounds it sleeps
instead of polling the RPC.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import time

from bot.client import PredictionClient
from bot.config import Config, load_config
from bot.strategy import Pools, decide, diluted_ev

log = logging.getLogger("prediction-bot")

#: Act only within this many seconds before lock (late odds are more informative).
BET_WINDOW_SECONDS = 10
#: Wake-up margin inside the window: decide ~8s before lock so the tx lands in time.
WAKE_MARGIN_SECONDS = BET_WINDOW_SECONDS - 2


def run_once(client: PredictionClient, cfg: Config, fee: float, handled: set[int]) -> float:
    """One scheduling step. Returns how long to sleep before the next one.

    ``handled`` collects epochs this process has already acted on: if an error
    strikes after a bet is broadcast (e.g. during the claim sweep), the retry
    lands back inside the same betting window and must not bet twice.
    """
    epoch = client.current_epoch()
    rnd = client.get_round(epoch)
    ttl = rnd.lock_ts - client.chain_time()

    if ttl <= 0:
        return 5.0  # lock passed; wait for the next round to start
    if ttl > BET_WINDOW_SECONDS:
        return max(2.0, ttl - WAKE_MARGIN_SECONDS)  # sleep until the betting window
    if epoch in handled:
        return 10.0  # already acted this round; wait out the lock

    # Marked before any side effect: on an ambiguous failure we prefer
    # skipping one round to double-betting it.
    handled.add(epoch)

    pools = Pools(bull=rnd.bull, bear=rnd.bear)
    side = decide(pools, cfg.ev_threshold, fee, stake=cfg.bet_amount_bnb)
    if side is None:
        log.info("epoch %d: no bet (bull %.2f / bear %.2f BNB)", epoch, rnd.bull, rnd.bear)
    else:
        ev = diluted_ev(pools, side, cfg.bet_amount_bnb, fee)
        if cfg.dry_run:
            log.info(
                "epoch %d: DRY RUN — would bet %s for %.4f BNB (diluted EV %+.3f)",
                epoch, side, cfg.bet_amount_bnb, ev,
            )
        else:
            tx = client.bet(side, epoch, cfg.bet_amount_bnb)
            log.info(
                "epoch %d: bet %s for %.4f BNB (diluted EV %+.3f) tx=%s",
                epoch, side, cfg.bet_amount_bnb, ev, tx,
            )

    if not cfg.dry_run:
        try:
            _sweep_claims(client, cfg)
        except Exception as exc:  # claims are retried next round; never re-enter the bet path
            log.warning("claim sweep failed (will retry next round): %s", exc)
    return 260.0  # this round is done for us; next lock is ~5 minutes out


def _sweep_claims(client: PredictionClient, cfg: Config) -> None:
    epochs = client.claimable_epochs(cfg.claim_lookback)
    if epochs:
        tx = client.claim(epochs)
        log.info("claimed %d round(s) %s tx=%s", len(epochs), epochs, tx)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="send real transactions (overrides DRY_RUN in the environment)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config()
    if args.live:
        cfg = dataclasses.replace(cfg, dry_run=False)
        if not cfg.wallet_address or not cfg.private_key:
            raise SystemExit("--live requires WALLET_ADDRESS and PRIVATE_KEY in the environment")

    client = PredictionClient(cfg)
    fee = client.treasury_fee()
    log.info(
        "connected — epoch %d, treasury fee %.1f%%, threshold %.2f, %s",
        client.current_epoch(), 100 * fee, cfg.ev_threshold,
        "DRY RUN" if cfg.dry_run else f"LIVE, betting {cfg.bet_amount_bnb} BNB",
    )

    handled: set[int] = set()  # grows ~288 epochs/day; trivial for any realistic run
    backoff = 5.0
    while True:
        try:
            sleep_s = run_once(client, cfg, fee, handled)
            backoff = 5.0
        except KeyboardInterrupt:
            log.info("stopping")
            return
        except Exception as exc:  # RPC hiccups are routine; retry with backoff
            log.warning("error: %s — retrying in %.0fs", exc, backoff)
            time.sleep(backoff)
            backoff = min(60.0, backoff * 2)
            continue
        time.sleep(sleep_s)


if __name__ == "__main__":
    main()
