from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..controllers.portfolio_controller import PortfolioController
from ..views.schemas.schemas import PortfolioResponse
from ..dependencies import get_db
from typing import List

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/{userid}", response_model=List[PortfolioResponse])
def get_user_portfolio(userid: int, db: Session = Depends(get_db)):
    return PortfolioController(db).get_user_portfolio(userid)
