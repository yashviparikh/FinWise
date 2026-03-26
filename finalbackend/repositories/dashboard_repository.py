from sqlalchemy.orm import Session
from ..models.models import Users, Portfolio
from typing import Optional

class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_data(self, userid: int):
        user = self.db.query(Users).filter(Users.userid == userid).first()
        portfolios = self.db.query(Portfolio).filter(Portfolio.userid == userid).all()
        return user, portfolios
