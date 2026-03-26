from pydantic import BaseModel
from typing import Optional, List

class UserBase(BaseModel):
    name: str
    email: str
    money: Optional[float] = 10000
    profitorloss: Optional[float] = 0
    profitpercent: Optional[float] = 0.0
    losspercent: Optional[float] = 0.0
    last_login: Optional[str] = None
    progress: Optional[int] = 0
    level: Optional[int] = 0

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    userid: int

class StockBase(BaseModel):
    stock_symbol: str
    stock_name: Optional[str] = None

class StockResponse(StockBase):
    stock_id: int

class WatchlistBase(BaseModel):
    user_id: int
    stock_id: int

class WatchlistResponse(WatchlistBase):
    watchlist_id: int

class PortfolioBase(BaseModel):
    userid: int
    stockname: str
    companyname: str
    totalquantity: int
    averagebuyprice: float
    totalinvested: float
    stock_id: int
    sector: Optional[str] = None

class PortfolioResponse(PortfolioBase):
    portfolioid: int

# Add more schemas as needed for other models and endpoints
