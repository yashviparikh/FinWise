from sqlalchemy.orm import Session
from ..models.models import Watchlist
from typing import List, Optional

class WatchlistRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user(self, user_id: int) -> List[Watchlist]:
        return self.db.query(Watchlist).filter(Watchlist.user_id == user_id).all()

    def add(self, watchlist: Watchlist):
        self.db.add(watchlist)
        self.db.commit()
        self.db.refresh(watchlist)
        return watchlist

    def remove(self, user_id: int, stock_id: int) -> bool:
        entry = self.db.query(Watchlist).filter_by(user_id=user_id, stock_id=stock_id).first()
        if entry:
            self.db.delete(entry)
            self.db.commit()
            return True
        return False
