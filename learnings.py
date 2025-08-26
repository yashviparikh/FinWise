from datetime import datetime
import os
import json
import requests
from summarizermodel import summarize_news
def getheadlines():
    url="https://gnews.io/api/v4/search?q=stock%20market&lang=en&country=in&token=806590bf32b625657aa33acc223d405b"
    headlines=requests.get(url)
    if headlines.status_code==200:
        data=headlines.json()
        articles = data.get("articles", [])[:10]  
        cleaned_articles = []
        for article in articles:
            cleaned = {
                "title": article.get("title", "").strip(),
                "description": article.get("description", "").strip(),
                "content": article.get("content", "").strip(),
                "url": article.get("url"),
                "image": article.get("image"),
                "publishedAt": article.get("publishedAt"),
                "source_name": article.get("source", {}).get("name"),
                "source_url": article.get("source", {}).get("url")
            }
            cleaned_articles.append(cleaned)

        return cleaned_articles     
    else: 
        print("error:",headlines.status_code)
# headlines=getheadlines()
# for i in headlines:
#     print(i,"\n")
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
        latest = getheadlines()
        summary=summarize_news()
        if latest:
            json_data = {
                "last_updated": datetime.now().isoformat(),
                "headline": latest["title"],
                "summary": summary,
                "sentiment": "this is the sentiment",
                "impact": "this is the market impact"
            }
        with open(cache_path, "w") as file:
            json.dump(json_data, file, indent=2)

    return json_data
# print(get_news())