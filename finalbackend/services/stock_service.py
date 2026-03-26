from ..repositories.stock_repository import StockRepository
from typing import Optional

class StockService:
    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    def get_stock(self, symbol: str):
        return self.stock_repository.get_by_symbol(symbol)

    def list_stocks(self):
        return self.stock_repository.get_all()
