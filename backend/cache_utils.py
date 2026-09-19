# Find the cache directory, all sectors, and all tickers for a given sector. Also get the last cached date for a given symbol and sector.

from datetime import date
import os
import logging
import pandas as pd
import tickers

# directory where cached CSV files are stored
def get_cache_directory(sector: str) -> str:
    return f"data/cache/{sector}/"

# get a list of all sectors and all tickers for a given sector
def get_all_symbol_sector_pairs() -> list[tuple[str, str]]:
    return [
        (symbol, sector)
        for sector, symbols in tickers.TICKERS.items()
        for symbol in symbols
    ]

# get sector list
def get_sector_list() -> list[str]:
    return list(tickers.TICKERS.keys())

# get all tickers for a given sector
def get_all_tickers(sector: str) -> list[str]:
    return list(tickers.TICKERS.get(sector, []))

# Get the last cached date for a given symbol and sector. Returns None if no cached data exists or if the CSV is empty or malformed.
def get_last_cached_date(symbol: str, sector: str) -> date | None:
    path = os.path.join(get_cache_directory(sector), f"{symbol}.csv")
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

