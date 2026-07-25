import pandas as pd
import tickers
from schemas import StockInfo, HistoryPoint, PredictionResponse
from predict import predict_for_symbol
from fastapi import FastAPI, HTTPException

app = FastAPI()

# for stock info endpoint
@app.get("/stocks", response_model=list[StockInfo])
def get_stocks():
    return tickers.TICKERS

# for history endpoint
@app.get("/history/{symbol}", response_model=list[HistoryPoint])
def get_history(symbol: str):
    if symbol not in [s['symbol'] for s in tickers.TICKERS]:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    try:
        df = pd.read_csv(f"data/cache/{symbol}.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No history data found for symbol {symbol}")

    return df.to_dict(orient='records')

# for prediction endpoint
@app.get("/predict/{symbol}", response_model=PredictionResponse)
def get_prediction(symbol: str):
    if symbol not in [s['symbol'] for s in tickers.TICKERS]:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    prediction_result = predict_for_symbol(symbol)
    if "error" in prediction_result:
        raise HTTPException(status_code=500, detail=prediction_result["error"]) 

    return prediction_result