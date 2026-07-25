'''
Predict stock prices using trained models.
'''

import pandas as pd
import joblib
from train_model import define_feature_target_columns
import logging

logging.basicConfig(level=logging.INFO)

# load all 4 models at module level, using joblib for each .pkl file
models = {
    "1w": joblib.load("model/model_target_1w.pkl"),
    "2w": joblib.load("model/model_target_2w.pkl"),
    "3w": joblib.load("model/model_target_3w.pkl"),
    "4w": joblib.load("model/model_target_4w.pkl"),
}

# load prediction_rows.csv from data
prediction_rows = pd.read_csv("data/prediction_rows.csv")

# filter prediction_rows to just the latest row per symbol, using groupby and idxmax on the date column
latest_prediction_rows = prediction_rows.loc[prediction_rows.groupby('symbol')['date'].idxmax()]

#store the exact feature column list imported from train_model.py
feature_columns = define_feature_target_columns(prediction_rows)[0]

# predict for symbols in latest_prediction_rows using the loaded models and feature_columns, and return a dataframe with the predictions
def predict_for_symbol(symbol: str) -> dict:
    row = latest_prediction_rows[latest_prediction_rows['symbol'] == symbol]
    if row.empty:
        return {"symbol": symbol, "error": f"No data available for symbol {symbol}"}

    features = row[feature_columns]

    # extract close price as a numeric scalar
    close_val = row['close'].iat[0]
    close_num = pd.to_numeric(close_val, errors='coerce')
    if pd.isna(close_num):
        logging.error(f"Invalid or missing close price for symbol {symbol}: {close_val}")
        return {"symbol": symbol, "error": f"Invalid or missing close price for symbol {symbol}"}
    current_close = float(close_num)

    predictions = {}
    try:
        for horizon, model in models.items():
            predicted_return = float(model.predict(features)[0])
            predictions[horizon] = {
                "return": predicted_return,
                "amount": round(current_close * (1 + predicted_return), 3)
            }

    except Exception as e:
        logging.error(f"Prediction failed for symbol {symbol}: {str(e)}")
        return {"symbol": symbol, "error": f"Prediction failed for symbol {symbol}: {str(e)}"}

    return {"symbol": symbol, "current_price": current_close, "predictions": predictions}

