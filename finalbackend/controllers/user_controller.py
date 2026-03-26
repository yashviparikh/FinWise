from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..services.user_service import UserService
from ..repositories.user_repository import UserRepository
from ..views.schemas.schemas import UserCreate, UserResponse
from ..dependencies import get_db

class UserController:
    def __init__(self, db: Session = Depends(get_db)):
        self.user_service = UserService(UserRepository(db))

    def signup(self, user: UserCreate):
        created_user = self.user_service.signup(user.name, user.email, user.password)
        return UserResponse(userid=created_user.userid, name=created_user.name, email=created_user.email)

    def login(self, email: str, password: str):
        user = self.user_service.login(email, password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user
