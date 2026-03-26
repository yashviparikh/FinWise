from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..controllers.auth_controller import AuthController
from ..dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/send-otp")
def send_otp(email: str, db: Session = Depends(get_db)):
    return AuthController(db).send_otp(email)

@router.post("/verify-otp")
def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    return AuthController(db).verify_otp(email, otp)

@router.post("/reset-password")
def reset_password(email: str, otp: str, new_password: str, db: Session = Depends(get_db)):
    return AuthController(db).reset_password(email, otp, new_password)
