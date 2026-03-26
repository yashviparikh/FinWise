from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from ..controllers.recommend_controller import RecommendController

class RecommendRequest(BaseModel):
    transactions: list
    stocks: list
    top_n: int = 5

router = APIRouter(prefix="/recommend", tags=["recommend"])

@router.post("/top-stocks")
def recommend_top_stocks(request: RecommendRequest):
    return RecommendController().recommend(request.transactions, request.stocks, request.top_n)
