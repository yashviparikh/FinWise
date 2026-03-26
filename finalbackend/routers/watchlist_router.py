from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..controllers.watchlist_controller import WatchlistController
from ..views.schemas.schemas import WatchlistBase, WatchlistResponse
from ..dependencies import get_db
from typing import List

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

@router.get("/{user_id}", response_model=List[WatchlistResponse])
def get_user_watchlist(user_id: int, db: Session = Depends(get_db)):
    return WatchlistController(db).get_user_watchlist(user_id)

@router.post("/add", response_model=WatchlistResponse)
def add_to_watchlist(watchlist: WatchlistBase, db: Session = Depends(get_db)):
    return WatchlistController(db).add_to_watchlist(watchlist)

@router.delete("/remove")
def remove_from_watchlist(user_id: int, stock_id: int, db: Session = Depends(get_db)):
    return WatchlistController(db).remove_from_watchlist(user_id, stock_id)
