from ..repositories.auth_repository import AuthRepository
from passlib.hash import bcrypt
from datetime import datetime, timedelta
import random

class AuthService:
    def __init__(self, auth_repository: AuthRepository):
        self.auth_repository = auth_repository

    def generate_otp(self, n: int = 6) -> str:
        return ''.join(str(random.randint(0, 9)) for _ in range(n))

    def send_otp(self, user, otp: str):
        # In production, send via email provider. For dev, just log it.
        print(f"[DEV OTP] email={user.email} otp={otp}")
        return True

    def verify_otp(self, user, otp: str) -> bool:
        if user.otp_code != otp:
            return False
        if datetime.utcnow() - user.otp_ts > timedelta(minutes=10):
            return False
        return True

    def reset_password(self, user, new_password: str):
        password_hash = bcrypt.hash(new_password)
        return self.auth_repository.update_password(user, password_hash)
