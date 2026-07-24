'''load and combine cached datasets for training'''

import logging
import pandas as pd
import tickers

# Loop through all tickers and load their cached data and sort by ascending date
def load_cached_data() -> dict[str, pd.DataFrame]:
    combined_data : dict[str, pd.DataFrame] = {}
    for ticker in tickers.TICKERS:
        symbol = ticker["symbol"]
        try:
            data = pd.read_csv(f"data/cache/{symbol}.csv")
            data['date'] = pd.to_datetime(data['date'])
            data.sort_values(by='date', inplace=True)
            data = data[~((data['high'] < data[['open', 'close', 'low']].max(axis=1)) | (data['low'] > data[['open', 'close', 'high']].min(axis=1)))]
            combined_data[symbol] = data
            logging.info(f"Loaded cached data for {symbol} with {len(data)} rows.")
        except FileNotFoundError:
            logging.warning(f"Cached data for {symbol} not found.")
    logging.info(f"Loaded {len(combined_data)} cached datasets.")
    return combined_data

# Attach the ticker symbol and sector as a new column on that dataframe
def attach_ticker_info(combined_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    for ticker in tickers.TICKERS:
        symbol = ticker["symbol"]
        sector = ticker["sector"]
        if symbol in combined_data:
            combined_data[symbol]['symbol'] = symbol
            combined_data[symbol]['sector'] = sector
    logging.info(f"Attached ticker info for {len(combined_data)} symbols.")
    return pd.concat(combined_data.values(), ignore_index=True)

# Main function to load and combine cached datasets for training into one dataframe
def load_and_combine_cached_data() -> pd.DataFrame:
    combined_data = load_cached_data()
    if not combined_data:
        logging.error("No cached data found for any tickers.")
        return pd.DataFrame()
    final_df = attach_ticker_info(combined_data)
    logging.info(f"Combined cached data into final dataframe with {len(final_df)} rows.")
    return final_df

if __name__ == "__main__":
    df = load_and_combine_cached_data()
    print(df.shape)
    print(df.head())