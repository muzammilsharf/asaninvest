'''load and combine cached datasets for training'''

import logging
import pandas as pd
import tickers

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import os

logging.basicConfig(level=logging.INFO)

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

# build feature set for training i.e. daily return, moving averages, volatility, volume change and target variables
def build_feature_set(df: pd.DataFrame) -> pd.DataFrame:
    df['daily_return'] = df.groupby('symbol')['close'].pct_change()
    df['ma_5'] = df['close'] / df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=5).mean())
    df['ma_20'] = df['close'] / df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=20).mean())
    df['volatility'] = df.groupby('symbol')['daily_return'].transform(lambda x: x.rolling(window=5).std())
    df['volume_change'] = df.groupby('symbol')['volume'].pct_change()
    df['target_1w'] = (df.groupby('symbol')['close'].shift(-5) - df['close']) / df['close']
    df['target_2w'] = (df.groupby('symbol')['close'].shift(-10) - df['close']) / df['close']
    df['target_3w'] = (df.groupby('symbol')['close'].shift(-15) - df['close']) / df['close']
    df['target_4w'] = (df.groupby('symbol')['close'].shift(-20) - df['close']) / df['close']
    logging.info(f"Built feature set with {len(df)} rows.")
    return df

# extract prediction rows (i.e. rows with NaN values in target columns) and save them to a separate CSV file for later use
def extract_prediction_rows(df: pd.DataFrame) -> pd.DataFrame:
    prediction_rows = df[df[['target_1w', 'target_2w', 'target_3w', 'target_4w']].isnull().any(axis=1)]
    prediction_rows.to_csv("data/prediction_rows.csv", index=False)
    logging.info(f"Extracted {len(prediction_rows)} prediction rows and saved to data/prediction_rows.csv.")
    return prediction_rows

# clean the dataframe by dropping rows with NaN values and keeps these rows aside for further analysis and resetting the index
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    initial_row_count = len(df)
    df.dropna(inplace=True)
    dropped_rows = initial_row_count - len(df)
    logging.info(f"Dropped {dropped_rows} rows with NaN values from the dataframe.")
    df.reset_index(drop=True, inplace=True)
    logging.info(f"Cleaned dataframe with {len(df)} rows after dropping NaN values.")
    return df

# encode sector as a numerical feature using one-hot encoding and drop the original sector column
def encode_sector(df: pd.DataFrame) -> pd.DataFrame:
    df = pd.get_dummies(df, columns=['sector'], prefix='sector')
    logging.info(f"Encoded sector into one-hot features. New dataframe has {len(df.columns)} columns.")
    return df

# define feature columns list and target columns list for training
def define_feature_target_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    feature_columns = ['daily_return', 'ma_5', 'ma_20', 'volatility', 'volume_change'] + [col for col in df.columns if col.startswith('sector_')]
    target_columns = ['target_1w', 'target_2w', 'target_3w', 'target_4w']
    logging.info(f"Defined {len(feature_columns)} feature columns and {len(target_columns)} target columns.")
    return feature_columns, target_columns

# train-test split the dataframe into training and testing sets from specific date range and return the split dataframes
def split_train_test(df: pd.DataFrame, test_start_date: str | pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    test_start_date = pd.to_datetime(test_start_date)
    train_df = df[df['date'] < test_start_date]
    test_df = df[df['date'] >= test_start_date]
    logging.info(f"Split data into training set with {len(train_df)} rows and testing set with {len(test_df)} rows.")
    return train_df, test_df

# run the entire data loading, feature engineering, and train-test split process
def run_data_preprocessing(test_start_date: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    df = load_and_combine_cached_data()
    if df.empty:
        logging.error("No data available for preprocessing.")
        return pd.DataFrame(), pd.DataFrame(), [], []
    df = build_feature_set(df)
    df = encode_sector(df)
    extract_prediction_rows(df)
    df = clean_dataframe(df)
    feature_columns, target_columns = define_feature_target_columns(df)
    train_df, test_df = split_train_test(df, test_start_date)
    return train_df, test_df, feature_columns, target_columns

# train the model using the training set and return the trained model
def train_models(train_df: pd.DataFrame, test_df: pd.DataFrame, feature_columns: list[str], target_columns: list[str]) -> tuple[dict[str, object], dict[str, float]]:

    models = {}
    mae_scores = {}

    os.makedirs("model", exist_ok=True)

    for target in target_columns:
        logging.info(f"Training model for {target}...")
        model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
        model.fit(train_df[feature_columns], train_df[target])
        models[target] = model

        predictions = model.predict(test_df[feature_columns])
        mae = mean_absolute_error(test_df[target], predictions)
        mae_scores[target] = mae
        logging.info(f"Model for {target} trained with MAE: {mae:.4f}")

        # Save the model
        joblib.dump(model, f"model/model_{target}.pkl", compress=3)
        logging.info(f"Model for {target} saved to model/model_{target}.pkl")

    return models, mae_scores

if __name__ == "__main__":
    train_df, test_df, feature_columns, target_columns = run_data_preprocessing("2026-03-01")

    if train_df.empty:
        logging.error("Preprocessing failed, aborting training.")
    else:
        models, mae_scores = train_models(train_df, test_df, feature_columns, target_columns)
        logging.info("Training complete. MAE per horizon:")
        for target, mae in mae_scores.items():
            logging.info(f"  {target}: {mae:.4f}")