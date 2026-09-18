# Fetch stock data for all tickers using psxdata and save it to data/cache directory. If any ticker fails to fetch, it will be logged in the console.
import os
import logging
import time
import tickers
import psxdata
import pandas as pd
from datetime import date, timedelta

FULL_HISTORY_START = date(2024, 1, 1)
END = date.today()
logging.basicConfig(level=logging.INFO)
REQUEST_DELAY_SECONDS = 2 

# Ensure that the cache directory exists.
def ensure_cache_directories_exists() -> None:
    for key in tickers.TICKERS:
        sector = key
        os.makedirs(f"data/cache/{sector}", exist_ok=True)

# Return the most recent date already cached for a symbol
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


# Fetch data for a single ticker over a specific date range.
def fetch_ticker_data(symbol: str, start: date, end: date) -> dict:
    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        data = psxdata.stocks(symbol, start, end)
        if data.empty:
            logging.info(f"No new data for {symbol} between {start} and {end}.")
            return {"success": False, "symbol": symbol, "empty": True}
        return {"success": True, "symbol": symbol, "data": data}
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        return {"success": False, "symbol": symbol, "empty": False}


# Save data for a single ticker to CSV, either as a fresh file or appended to an existing one. When appending, rows already present (by date) are dropped first as a safety net against duplicates.
def save_ticker_data(symbol: str, sector: str, data: pd.DataFrame, append: bool) -> None:
    path = f"data/cache/{sector}/{symbol}.csv"
 
    if append and os.path.exists(path):
        existing = pd.read_csv(path)
        existing["date"] = pd.to_datetime(existing["date"])
        data["date"] = pd.to_datetime(data["date"])
        new_rows = data[~data["date"].isin(existing["date"])]
 
        if new_rows.empty:
            logging.info(f"No genuinely new rows for {symbol}, skipping write.")
            return
 
        new_rows.to_csv(path, mode="a", header=False, index=False)
        logging.info(f"Appended {len(new_rows)} new row(s) for {symbol} to {path}.")
    else:
        data.to_csv(path, index=False)
        logging.info(f"Data for {symbol} saved to {path} with {len(data)} rows.")


# Fetch data for a single ticker with retry logic, using an incremental date range based on what's already cached.
def fetch_and_save_with_retry(symbol: str, sector: str) -> bool:
    last_date = get_last_cached_date(symbol, sector)
    append = last_date is not None
 
    if append:
        start = last_date + timedelta(days=1)
        if start > END:
            logging.info(f"{symbol} is already up to date, nothing to fetch.")
            return True
    else:
        start = FULL_HISTORY_START
 
    result = fetch_ticker_data(symbol, start, END)
    if result["success"]:
        save_ticker_data(symbol, sector, result["data"], append)
        return True
 
    if result.get("empty"):
        # No new trading data for this range, not a failure.
        return True
 
    logging.info(f"Retrying fetch for {symbol}...")
    time.sleep(REQUEST_DELAY_SECONDS)
    retry_result = fetch_ticker_data(symbol, start, END)
    if retry_result["success"]:
        save_ticker_data(symbol, sector, retry_result["data"], append)
        return True
    if retry_result.get("empty"):
        return True
 
    logging.error(f"Failed to fetch data for {symbol} after retry.")
    return False
 
# Fetch data for all tickers and save to cache, sector by sector.
def fetch_data() -> None:
    ensure_cache_directories_exists()
    failed_tickers: list = []
 
    for sector, companies in tickers.TICKERS.items():
        logging.info(f"--- Processing sector: {sector} ({len(companies)} tickers) ---")
        for symbol, name in companies.items():
            logging.info(f"Fetching data for {symbol} ({name}) - {sector}...")
            if not fetch_and_save_with_retry(symbol, sector):
                failed_tickers.append(symbol)
 
    if failed_tickers:
        logging.warning(f"Failed to fetch data for the following tickers: {', '.join(failed_tickers)}")
    else:
        logging.info("All tickers processed successfully.")


if __name__ == "__main__":
    fetch_data()