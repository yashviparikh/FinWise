from ..repositories.user_repository import UserRepository
from passlib.hash import bcrypt
from typing import Optional

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def signup(self, name: str, email: str, password: str):
        password_hash = bcrypt.hash(password)
        return self.user_repository.create(name, email, password_hash)

    def login(self, identifier: str, password: str) -> Optional[dict]:
        user = self.user_repository.get_by_email(identifier)
        if user and bcrypt.verify(password, user.password_hash):
            self.user_repository.update_last_login(user)
            return {"userid": user.userid, "name": user.name, "email": user.email}
        return None
