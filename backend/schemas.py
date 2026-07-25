''' pydantic models for endpoint schemas'''

from pydantic import BaseModel

# for stock info endpoint
class StockInfo(BaseModel):
    symbol: str
    name: str
    sector: str

# for history point
class HistoryPoint(BaseModel):
    date: str
    close: float
    open : float
    high: float
    low: float
    volume: int

# for prediction response
class PredictionResponse(BaseModel):
    symbol: str
    predictions: dict[str, float]