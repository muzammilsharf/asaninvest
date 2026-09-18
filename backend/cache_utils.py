# Return the most recent date already cached for a symbol used in fetching data and checking data

from datetime import date
import os
import logging
import pandas as pd


def get_last_cached_date(symbol: str, sector: str) -> date | None:
    path = f"data/cache/{sector}/{symbol}.csv"
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        if df.empty or "date" not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"])
        return df["date"].max().date()
    except Exception as e:
        logging.error(f"Could not read cached file for {symbol}: {e}")
        return None