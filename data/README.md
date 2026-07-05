# Round history dataset

`rounds.csv.gz` — one row per PancakeSwap Prediction (BNB/USD, V2) round,
epochs 100–144,099, 26 Aug 2021 → 6 Feb 2023 (UTC), collected from the
[`PancakePredictionV2`](https://bscscan.com/address/0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA)
contract's public `rounds()` view.

Read it directly with pandas:

```python
import pandas as pd
df = pd.read_csv("data/rounds.csv.gz")
```

## Schema

| Column | Unit | Description |
|---|---|---|
| `epoch` | — | Round id (contract epoch) |
| `startTimestamp` | Unix s (UTC) | Betting opens |
| `lockTimestamp` | Unix s (UTC) | Betting closes; lock price recorded |
| `closeTimestamp` | Unix s (UTC) | Round resolves; close price recorded |
| `lockPrice` | USD × 1e8 | Chainlink BNB/USD at lock |
| `closePrice` | USD × 1e8 | Chainlink BNB/USD at close |
| `lockOracleId` / `closeOracleId` | — | Chainlink round ids |
| `totalAmount` | wei (1e18) | Total pool |
| `bullAmount` / `bearAmount` | wei (1e18) | Side pools |
| `rewardBaseCalAmount` | wei (1e18) | Winning side's pool (payout denominator) |
| `rewardAmount` | wei (1e18) | Distributed pool = `totalAmount × (1 − fee)` |
| `oracleCalled` | bool | Round settled normally (else refunded) |

Outcome definition: **Bull** wins iff `closePrice > lockPrice`, **Bear** wins
iff `closePrice < lockPrice`; on an exact tie the house keeps the pool.
A winning 1-unit stake pays `rewardAmount / rewardBaseCalAmount` (stake included).

## Caveats

- The `*Amount` columns were exported in scientific notation with ~6
  significant digits, so values carry ~1e-6 relative error — irrelevant for
  payout ratios, but don't treat them as exact wei integers.
- Some rounds have `oracleCalled = False` (cancelled/refunded) or an empty
  side pool; the research pipeline excludes them from the clean sample.
