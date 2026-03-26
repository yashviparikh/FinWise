from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.dashboard_service import DashboardService
from ..repositories.dashboard_repository import DashboardRepository
from ..dependencies import get_db

class DashboardController:
    def __init__(self, db: Session = Depends(get_db)):
        self.dashboard_service = DashboardService(DashboardRepository(db))

    def get_dashboard(self, userid: int):
        data = self.dashboard_service.get_dashboard(userid)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
