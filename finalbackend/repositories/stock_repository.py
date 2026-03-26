from sqlalchemy.orm import Session
from ..models.models import Stock
from typing import Optional

class StockRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        return self.db.query(Stock).filter(Stock.stock_symbol == symbol).first()

    def get_all(self):
        return self.db.query(Stock).all()
