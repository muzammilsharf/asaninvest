# Find the cache directory, all sectors, and all tickers for a given sector. Also get the last cached date for a given symbol and sector.

from datetime import date
import os
import logging
import pandas as pd

# directory where cached CSV files are stored
def get_cache_directory(sector: str) -> str:
    return f"data/cache/{sector}/"

# Get a list of all sectors for which cached data exists
def get_sector_list() -> list[str]:
    return [d for d in os.listdir("data/cache") if os.path.isdir(os.path.join("data/cache", d))]

# get all the tickers symbols for a given sector
def get_tickers_for_sector(sector: str) -> list[str]:
    path = get_cache_directory(sector)
    if not os.path.exists(path):
        return []
    return [f.split(".csv")[0] for f in os.listdir(path) if f.endswith(".csv")] 

# get all the tickers symbols for all sectors
def get_all_tickers() -> list[str]:
    tickers = []
    for sector in get_sector_list():
        tickers.extend(get_tickers_for_sector(sector))
    return tickers

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

