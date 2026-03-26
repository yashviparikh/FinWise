from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..controllers.stock_controller import StockController
from ..dependencies import get_db

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("/{symbol}")
def get_stock(symbol: str, db: Session = Depends(get_db)):
    return StockController(db).get_stock(symbol)

@router.get("/")
def list_stocks(db: Session = Depends(get_db)):
    return StockController(db).list_stocks()
