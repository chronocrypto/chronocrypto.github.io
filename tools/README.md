# Hive transaction export

Utility script to export Hive account transactions to CSV files. It uses the
public Hive condenser API, supports multiple fallback nodes, and writes a CSV
with direction, sender, recipient, currency, and amount columns.

## Usage

```
python tools/hive_tx_to_csv.py <account> [<account> ...] --start YYYY-MM-DD --end YYYY-MM-DD --output my_txs.csv
```

Flags:
- `--start` / `--end`: inclusive date range in UTC.
- `--output`: output CSV path (defaults to `hive_transactions.csv`).
- `--node`: optional additional condenser node URLs; can be provided multiple times for redundancy.

The resulting CSV includes the source account in an `account` column so that
combined exports remain easy to filter.
