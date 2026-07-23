"""
Data quality checks for cached PSX ticker data.

"""

import os
import logging
import pandas as pd
import tickers

logging.basicConfig(level=logging.INFO)

CACHE_DIR = "data/cache"
MIN_HISTORY_DAYS = 365


def check_ticker(symbol: str) -> dict:
    result = {"symbol": symbol, "issues": []}
    path = os.path.join(CACHE_DIR, f"{symbol}.csv")

    if not os.path.exists(path):
        result["issues"].append("no cached CSV found, run fetch_data.py first")
        return result

    df = pd.read_csv(path)

    if df.empty:
        result["issues"].append("CSV is empty")
        return result

    # figure out which column is the date column, whatever it's named
    date_col = "date" if "date" in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)

    result["rows"] = len(df)
    result["date_range"] = f"{df[date_col].min().date()} to {df[date_col].max().date()}"

    # 1. enough history
    if len(df) < MIN_HISTORY_DAYS:
        result["issues"].append(f"only {len(df)} rows, want {MIN_HISTORY_DAYS}+")

    # 2. duplicate dates
    dup_count = df[date_col].duplicated().sum()
    if dup_count > 0:
        result["issues"].append(f"{dup_count} duplicate dates")

    # 3. required columns present (case-insensitive match)
    required_cols = ["open", "high", "low", "close", "volume"]
    col_map = {c.lower(): c for c in df.columns}
    missing_cols = [c for c in required_cols if c not in col_map]
    if missing_cols:
        result["issues"].append(f"missing columns: {missing_cols}")
        result["status"] = "FAIL"
        return result

    open_c, high_c, low_c, close_c, vol_c = (
        col_map["open"], col_map["high"], col_map["low"], col_map["close"], col_map["volume"]
    )

    # 4. nulls
    nulls = df[[open_c, high_c, low_c, close_c, vol_c]].isnull().sum().sum()
    if nulls > 0:
        result["issues"].append(f"{nulls} null values across OHLCV")

    # 5. zero/negative prices
    zero_price_rows = (df[[open_c, high_c, low_c, close_c]] <= 0).any(axis=1).sum()
    if zero_price_rows > 0:
        result["issues"].append(f"{zero_price_rows} rows with zero/negative price")

    # 6. zero volume (more than 5% of rows)
    zero_volume_rows = (df[vol_c] == 0).sum()
    if zero_volume_rows > len(df) * 0.05:
        result["issues"].append(f"{zero_volume_rows} rows with zero volume (>5% of data)")

    # 7. OHLC logic: high should be the max, low should be the min
    bad_ohlc = (
        (df[high_c] < df[[open_c, close_c, low_c]].max(axis=1)) |
        (df[low_c] > df[[open_c, close_c, high_c]].min(axis=1))
    ).sum()
    if bad_ohlc > 0:
        result["issues"].append(f"{bad_ohlc} rows break High/Low logic")

    # 8. extreme one-day jumps (>25%), flag for manual review, not auto-fail
    pct_change = df[close_c].pct_change().abs()
    extreme_moves = (pct_change > 0.25).sum()
    if extreme_moves > 0:
        result["issues"].append(f"{extreme_moves} days with >25% price move, verify manually")

    result["status"] = "PASS" if not result["issues"] else "CHECK"
    return result


def main() -> None:
    symbols = [t["symbol"] for t in tickers.TICKERS]
    logging.info(f"Checking {len(symbols)} cached tickers in {CACHE_DIR}")

    summary = [check_ticker(symbol) for symbol in symbols]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in summary:
        status = r.get("status", "FAIL")
        print(f"\n[{status}] {r['symbol']}")
        if "rows" in r:
            print(f"  rows: {r['rows']}, range: {r['date_range']}")
        for issue in r["issues"]:
            print(f"  - {issue}")

    passed = sum(1 for r in summary if r.get("status") == "PASS")
    print(f"\n{passed}/{len(symbols)} tickers passed with no issues.")
    print("Tickers with issues aren't automatically unusable, review each")
    print("flag manually before deciding to drop or refetch a ticker.")


if __name__ == "__main__":
    main()