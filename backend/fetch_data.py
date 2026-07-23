# Fetch stock data for all tickers using psxdata and save it to data/cache directory. If any ticker fails to fetch, it will be logged in the console.
import os
import logging
import time
import tickers
import psxdata
from datetime import date, timedelta

LOOKBACK_DAYS : int = 730
START = date.today() - timedelta(days=LOOKBACK_DAYS)
END = date.today()
logging.basicConfig(level=logging.INFO)
REQUEST_DELAY_SECONDS = 2 

# Ensure that the cache directory exists.
def ensure_cache_directory_exists() -> None:
    os.makedirs("data/cache", exist_ok=True)

# Fetch data for a single ticker.
def fetch_ticker_data(symbol: str) -> dict:
    try:
        time.sleep(REQUEST_DELAY_SECONDS)
        data = psxdata.stocks(symbol, START, END)
        if data.empty:
            logging.warning(f"No data found for {symbol}.")
            return {"success": False, "symbol": symbol}
        return {"success": True, "symbol": symbol, "data": data}  
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {e}")
        return {"success": False, "symbol": symbol}

# Save data for a single ticker to CSV.
def save_ticker_data(symbol: str, data) -> None:
    data.to_csv(f"data/cache/{symbol}.csv", index=False)
    logging.info(f"Data for {symbol} saved to data/cache/{symbol}.csv with {len(data)} rows.")

# Fetch data for a single ticker with retry logic.
def fetch_and_save_with_retry(symbol: str) -> bool:
    result = fetch_ticker_data(symbol)
    if result["success"]:
        save_ticker_data(symbol, result["data"])
        return True
    else:
        time.sleep(REQUEST_DELAY_SECONDS)
        logging.info(f"Retrying fetch for {symbol}...")
        retry_result = fetch_ticker_data(symbol)
        if retry_result["success"]:
            save_ticker_data(symbol, retry_result["data"])
            return True
        else:
            logging.error(f"Failed to fetch data for {symbol} after retry.")
            return False

# Fetch data for all tickers and save to cache.
def fetch_data() -> None:
    ensure_cache_directory_exists()
    failed_tickers: list = []
    for ticker in tickers.TICKERS:
        symbol = ticker["symbol"]
        logging.info(f"Fetching data for {symbol}...")
        if not fetch_and_save_with_retry(symbol):
            failed_tickers.append(symbol)

    if failed_tickers:
        logging.warning(f"Failed to fetch data for the following tickers: {', '.join(failed_tickers)}")

if __name__ == "__main__":
    fetch_data()