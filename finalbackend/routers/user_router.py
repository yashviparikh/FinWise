from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..controllers.user_controller import UserController
from ..views.schemas.schemas import UserCreate, UserResponse
from ..dependencies import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    return UserController(db).signup(user)

@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    return UserController(db).login(email, password)
