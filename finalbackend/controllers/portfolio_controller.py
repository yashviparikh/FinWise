from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.portfolio_service import PortfolioService
from ..repositories.portfolio_repository import PortfolioRepository
from ..models.models import Portfolio
from ..views.schemas.schemas import PortfolioResponse
from ..dependencies import get_db
from typing import List

class PortfolioController:
    def __init__(self, db: Session = Depends(get_db)):
        self.portfolio_service = PortfolioService(PortfolioRepository(db))

    def get_user_portfolio(self, userid: int) -> List[PortfolioResponse]:
        portfolios = self.portfolio_service.get_user_portfolio(userid)
        return [PortfolioResponse(**p.__dict__) for p in portfolios]

    def add_portfolio(self, portfolio: Portfolio):
        return self.portfolio_service.add_portfolio(portfolio)
