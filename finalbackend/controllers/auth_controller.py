from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..services.auth_service import AuthService
from ..repositories.auth_repository import AuthRepository
from ..views.schemas.schemas import UserResponse
from ..dependencies import get_db

class AuthController:
    def __init__(self, db: Session = Depends(get_db)):
        self.auth_service = AuthService(AuthRepository(db))

    def send_otp(self, email: str):
        user = self.auth_service.auth_repository.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        otp = self.auth_service.generate_otp()
        self.auth_service.auth_repository.update_otp(user, otp, None)
        self.auth_service.send_otp(user, otp)
        return {"status": "success", "message": "OTP sent"}

    def verify_otp(self, email: str, otp: str):
        user = self.auth_service.auth_repository.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not self.auth_service.verify_otp(user, otp):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        return {"status": "success", "message": "OTP verified"}

    def reset_password(self, email: str, otp: str, new_password: str):
        user = self.auth_service.auth_repository.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not self.auth_service.verify_otp(user, otp):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        self.auth_service.reset_password(user, new_password)
        return {"status": "success", "message": "Password updated"}
