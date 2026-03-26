from fastapi import APIRouter
from ..controllers.learnings_controller import LearningsController

router = APIRouter(prefix="/learnings", tags=["learnings"])

@router.get("/news")
def get_news():
    return LearningsController().get_news()
