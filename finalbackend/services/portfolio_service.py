from ..repositories.portfolio_repository import PortfolioRepository
from ..models.models import Portfolio
from typing import List

class PortfolioService:
    def __init__(self, portfolio_repository: PortfolioRepository):
        self.portfolio_repository = portfolio_repository

    def get_user_portfolio(self, userid: int) -> List[Portfolio]:
        return self.portfolio_repository.get_by_user(userid)

    def add_portfolio(self, portfolio: Portfolio):
        return self.portfolio_repository.add(portfolio)
