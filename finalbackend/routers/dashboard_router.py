from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..controllers.dashboard_controller import DashboardController
from ..dependencies import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/{userid}")
def get_dashboard(userid: int, db: Session = Depends(get_db)):
    return DashboardController(db).get_dashboard(userid)
