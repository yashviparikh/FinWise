from fastapi import Depends
from sqlalchemy.orm import Session
from ..services.stock_service import StockService
from ..repositories.stock_repository import StockRepository
from ..views.schemas.schemas import StockResponse
from ..dependencies import get_db

class StockController:
    def __init__(self, db: Session = Depends(get_db)):
        self.stock_service = StockService(StockRepository(db))

    def get_stock(self, symbol: str):
        stock = self.stock_service.get_stock(symbol)
        if not stock:
            return None
        return StockResponse(stock_id=stock.stock_id, stock_symbol=stock.stock_symbol, stock_name=stock.stock_name)

    def list_stocks(self):
        stocks = self.stock_service.list_stocks()
        return [StockResponse(stock_id=s.stock_id, stock_symbol=s.stock_symbol, stock_name=s.stock_name) for s in stocks]
