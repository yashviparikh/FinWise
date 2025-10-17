from datetime import datetime
import os
import json
import requests
from invest.ragbased import impacttosentiment,getimpact,sentiment_to_market_action
def getheadlines():
    url="https://gnews.io/api/v4/search?q=stock%20market&lang=en&country=in&token=806590bf32b625657aa33acc223d405b"
    headlines=requests.get(url)
    if headlines.status_code==200:
        data=headlines.json()
        articles = data.get("articles", [])[:5]  
        cleaned_articles = []
        for article in articles:
            cleaned = {
                "title": article.get("title", "").strip(),
                "description": article.get("description", "").strip()
            }
            cleaned_articles.append(cleaned)
        return cleaned_articles     
    else: 
        print("error:",headlines.status_code)
# headlines=getheadlines()
# for i in headlines:
#     print(i,"\n")
def get_news():
    try:
        should_refresh = True
        json_data = {}
        cache_path = 'cache_news.json'

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as file:
                    json_data = json.load(file)
                    last_updated = datetime.fromisoformat(json_data.get('last_updated', '1970-01-01')).date()
                    if last_updated == datetime.now().date():
                        return json_data
            except Exception as e:
                print("❗ Cache read failed:", e)

        latest = getheadlines()
        if not latest:
            return {"error": "No news from API"}

        from invest.summarizermodel import summarize_news  

        newsdata = []
        for article in latest:
            try:
                desc = article.get("description") or article.get("content") or ""
                summary = desc if len(desc) < 20 else summarize_news(desc)
                impacts = getimpact(article["title"], summary)
                sentiment = impacttosentiment(impacts)
                reaction, action = sentiment_to_market_action(sentiment)
                newsdata.append({
                    "headline": article["title"],
                    "summary": summary,
                    "sentiment": sentiment,
                    "market reaction": reaction,
                    "investor reaction": action
                })
            except Exception as e:
                print("❗ Error processing article:", e)

        json_data = {
            "last_updated": datetime.now().isoformat(),
            "news": newsdata
        }
        with open(cache_path, "w") as file:
            json.dump(json_data, file, indent=2)

        return json_data
    except Exception as e:
        print("❗ Fatal error in get_news:", e)
        return {"error": str(e)}
# print(get_news())