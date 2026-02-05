# Temple to Bitwave Trade CSV Converter

A Streamlit web app that converts Temple platform trade fill exports into Bitwave-compatible CSV format.

## What It Does

The Temple platform exports trade data as individual **fills** — a single trade order can produce dozens or hundreds of fill rows. This app:

1. **Consolidates fills** by `trade_id` (summing amounts across all fills for each trade)
2. **Maps asset names** (`Amulet` → `CANTON`, `USDCx` → `USDC`)
3. **Generates two rows per trade**: a `tradeAcquire` row and a `tradeDispose` row
4. **Formats timestamps** using the earliest fill time for each trade
5. **Alerts on fees** if any non-zero fee values are detected

## Output Format

Each trade produces exactly two rows in the Bitwave format:

| Column | Description |
|--------|-------------|
| `id` | Unique random identifier |
| `amount` | Token quantity for this side of the trade |
| `amountTicker` | `CANTON` or `USDC` |
| `time` | Earliest fill timestamp (M/D/YY HH:MM) |
| `blockchainId` | Original `trade_id` from Temple |
| `transactionType` | `tradeAcquire` or `tradeDispose` |
| `taxExempt` | Always `FALSE` |
| `tradeId` | Sequential ID linking the acquire/dispose pair |

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

This app is deployed on [Streamlit Community Cloud](https://streamlit.io/cloud). Push changes to `main` and the app redeploys automatically.
