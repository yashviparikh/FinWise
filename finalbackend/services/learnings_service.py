import requests
from ..repositories.learnings_repository import LearningsRepository
from typing import Dict, Any

class LearningsService:
    def __init__(self, learnings_repository: LearningsRepository):
        self.learnings_repository = learnings_repository

    def get_news(self) -> Dict[str, Any]:
        cached = self.learnings_repository.get_cached_news()
        if cached:
            return cached
        url = "https://gnews.io/api/v4/search?q=stock%20market&lang=en&country=in&token=806590bf32b625657aa33acc223d405b"
        headlines = requests.get(url)
        if headlines.status_code == 200:
            data = headlines.json()
            articles = data.get("articles", [])[:5]
            cleaned_articles = [
                {"title": a.get("title", "").strip(), "description": a.get("description", "").strip()} for a in articles
            ]
            result = {"articles": cleaned_articles}
            self.learnings_repository.set_cached_news(result)
            return result
        return {"error": "Failed to fetch news"}
