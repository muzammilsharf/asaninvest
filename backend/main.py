import os
import pandas as pd
import cache_utils
from schemas import StockInfo, HistoryPoint, PredictionResponse
from predict import predict_for_symbol
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#for health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# for sectors endpoint
@app.get("/sectors", response_model=list[str])
def get_sectors():
    return cache_utils.get_sector_list()

@app.get("/{sector}/stocks", response_model=list[StockInfo])
def get_stocks(sector: str):
    if sector not in cache_utils.get_sector_list():
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    return [
        {"symbol": symbol, "name": cache_utils.get_ticker_name(symbol, sector), "sector": sector}
        for symbol in cache_utils.get_all_tickers(sector)
    ]

# for history endpoint
@app.get("/history/{sector}/{symbol}", response_model=list[HistoryPoint])
def get_history(sector: str, symbol: str):
    symbol_list = cache_utils.get_all_tickers(sector)
    if sector not in cache_utils.get_sector_list():
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    if symbol not in symbol_list:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    try:
        path = os.path.join(cache_utils.get_cache_directory(sector), f"{symbol}.csv")
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No history data found for symbol {symbol}")

    return df.to_dict(orient='records')

# for prediction endpoint
@app.get("/predict/{sector}/{symbol}", response_model=PredictionResponse)
def get_prediction(sector: str, symbol: str):
    symbol_list = cache_utils.get_all_tickers(sector)
    if sector not in cache_utils.get_sector_list():
        raise HTTPException(status_code=404, detail=f"Sector {sector} not found")
    if symbol not in symbol_list:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    prediction_result = predict_for_symbol(symbol)
    if "error" in prediction_result:
        raise HTTPException(status_code=500, detail=prediction_result["error"]) 

    return prediction_result