from ..repositories.watchlist_repository import WatchlistRepository
from ..models.models import Watchlist
from typing import List

class WatchlistService:
    def __init__(self, watchlist_repository: WatchlistRepository):
        self.watchlist_repository = watchlist_repository

    def get_user_watchlist(self, user_id: int) -> List[Watchlist]:
        return self.watchlist_repository.get_by_user(user_id)

    def add_to_watchlist(self, watchlist: Watchlist):
        return self.watchlist_repository.add(watchlist)

    def remove_from_watchlist(self, user_id: int, stock_id: int) -> bool:
        return self.watchlist_repository.remove(user_id, stock_id)
