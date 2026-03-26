from sqlalchemy.orm import Session
from ..models.models import Users
from typing import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[Users]:
        return self.db.query(Users).filter(Users.email == email).first()

    def get_by_id(self, userid: int) -> Optional[Users]:
        return self.db.query(Users).filter(Users.userid == userid).first()

    def create(self, name: str, email: str, password_hash: str):
        user = Users(name=name, email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_last_login(self, user: Users):
        from datetime import datetime
        user.last_login = datetime.utcnow()
        self.db.commit()
        return user
