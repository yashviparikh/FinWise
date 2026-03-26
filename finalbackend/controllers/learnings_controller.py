from fastapi import Depends
from ..services.learnings_service import LearningsService
from ..repositories.learnings_repository import LearningsRepository

class LearningsController:
    def __init__(self):
        self.learnings_service = LearningsService(LearningsRepository())

    def get_news(self):
        return self.learnings_service.get_news()
