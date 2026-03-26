from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.watchlist_service import WatchlistService
from ..repositories.watchlist_repository import WatchlistRepository
from ..models.models import Watchlist
from ..views.schemas.schemas import WatchlistResponse, WatchlistBase
from ..dependencies import get_db
from typing import List

class WatchlistController:
    def __init__(self, db: Session = Depends(get_db)):
        self.watchlist_service = WatchlistService(WatchlistRepository(db))

    def get_user_watchlist(self, user_id: int) -> List[WatchlistResponse]:
        watchlist = self.watchlist_service.get_user_watchlist(user_id)
        return [WatchlistResponse(**w.__dict__) for w in watchlist]

    def add_to_watchlist(self, watchlist: WatchlistBase):
        w = Watchlist(**watchlist.dict())
        return self.watchlist_service.add_to_watchlist(w)

    def remove_from_watchlist(self, user_id: int, stock_id: int):
        if not self.watchlist_service.remove_from_watchlist(user_id, stock_id):
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"message": "Removed from watchlist"}
