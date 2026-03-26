from fastapi import Depends
from ..services.recommend_service import RecommendService
from ..repositories.recommend_repository import RecommendRepository
import pandas as pd
from typing import List

class RecommendController:
    def __init__(self):
        self.recommend_service = RecommendService(RecommendRepository())

    def recommend(self, transactions: list, stocks: list, top_n: int = 5) -> List[dict]:
        transactions_df = pd.DataFrame(transactions)
        stocks_df = pd.DataFrame(stocks)
        return self.recommend_service.recommend_top_stocks(transactions_df, stocks_df, top_n)
