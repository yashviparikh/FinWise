from datetime import datetime
import os
import json

def get_news():
    should_refresh = True
    json_data = {}
    cache_path='cache_news.json'
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as file:
                json_data = json.load(file)
                last_updated = datetime.fromisoformat(json_data['last_updated']).date()
                if last_updated == datetime.now().date().isoformat():
                    should_refresh = False
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print("❗ Cache file invalid or corrupted:", e)

    if should_refresh:
        json_data = {
            "last_updated": datetime.now().isoformat(),
            "headline": "new headline",
            "summary": "this is some summary",
            "sentiment": "this is the sentiment",
            "impact": "this is the market impact"
        }
        with open(cache_path, "w") as file:
            json.dump(json_data, file, indent=2)

    return json_data
print(get_news())