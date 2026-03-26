from ..repositories.dashboard_repository import DashboardRepository
from typing import Dict

class DashboardService:
    def __init__(self, dashboard_repository: DashboardRepository):
        self.dashboard_repository = dashboard_repository

    def get_dashboard(self, userid: int) -> Dict:
        user, portfolios = self.dashboard_repository.get_dashboard_data(userid)
        if not user:
            return {"error": "User not found"}
        # Example: return user info and portfolio count
        return {
            "user": {"userid": user.userid, "name": user.name, "email": user.email},
            "portfolio_count": len(portfolios)
        }
