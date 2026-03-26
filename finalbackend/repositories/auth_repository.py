from sqlalchemy.orm import Session
from ..models.models import Users
from typing import Optional

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[Users]:
        return self.db.query(Users).filter(Users.email == email).first()

    def update_otp(self, user: Users, otp: str, otp_ts):
        user.otp_code = otp
        user.otp_ts = otp_ts
        self.db.commit()
        return user

    def update_password(self, user: Users, password_hash: str):
        user.password_hash = password_hash
        user.otp_code = None
        user.otp_ts = None
        self.db.commit()
        return user
