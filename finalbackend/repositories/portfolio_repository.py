from sqlalchemy.orm import Session
from ..models.models import Portfolio
from typing import Optional, List

class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, userid: int) -> List[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.userid == userid).all()

    def add(self, portfolio: Portfolio):
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def get_by_id(self, portfolioid: int) -> Optional[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.portfolioid == portfolioid).first()
