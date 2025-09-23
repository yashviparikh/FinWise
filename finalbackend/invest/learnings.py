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
    should_refresh = True
    json_data = {}
    cache_path='cache_news.json'
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as file:
                json_data = json.load(file)
                last_updated = datetime.fromisoformat(json_data['last_updated']).date()
                if last_updated == datetime.now().date():
                    return json_data  
                else:
                    should_refresh = True
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print("❗ Cache file invalid or corrupted:", e)

    if should_refresh:
        latest = getheadlines() 
        from invest.summarizermodel import summarize_news  
        if latest:
            newsdata = []
            for article in latest:
                desc = article.get("description") or article.get("content") or ""
                if len(desc) < 20: 
                    summary = desc
                else:
                    summary = summarize_news(desc)
                impacts=getimpact(article["title"],summary)
                sentiment=impacttosentiment(impacts)
                reaction,action = sentiment_to_market_action(sentiment)
                newsdata.append({
                    "headline": article["title"],
                    "summary": summary,
                    "sentiment": sentiment,
                    "market reaction": reaction,
                    "investor reaction":action
                })
        json_data = {
            "last_updated": datetime.now().isoformat(),
            "news": newsdata
            }
        with open(cache_path, "w") as file:
            json.dump(json_data, file, indent=2)

    return json_data
# print(get_news())