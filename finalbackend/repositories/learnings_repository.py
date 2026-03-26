import os
import json
from datetime import datetime
from typing import Dict, Any

class LearningsRepository:
    def __init__(self):
        self.cache_path = os.path.join(os.path.dirname(__file__), "..", "cache_news.json")

    def get_cached_news(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r") as file:
                    json_data = json.load(file)
                    last_updated = datetime.fromisoformat(json_data.get('last_updated', '1970-01-01')).date()
                    if last_updated == datetime.now().date():
                        return json_data
            except Exception:
                pass
        return {}

    def set_cached_news(self, data: Dict[str, Any]):
        data['last_updated'] = datetime.now().date().isoformat()
        with open(self.cache_path, "w") as file:
            json.dump(data, file)
