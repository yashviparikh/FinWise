from datetime import datetime
import os
import json
import requests
from ragbased import impacttosentiment,getimpact,sentiment_to_market_action
def getheadlines():
    url="https://gnews.io/api/v4/search?q=stock%20market&lang=en&country=in&token=806590bf32b625657aa33acc223d405b"
    print("1")
    headlines=requests.get(url)
    if headlines.status_code==200:
        data=headlines.json()
        articles = data.get("articles", [])[:5]  
        cleaned_articles = []
        print("2")
        for article in articles:
            cleaned = {
                "title": article.get("title", "").strip(),
                "description": article.get("description", "").strip()
            }
            cleaned_articles.append(cleaned)
        print("3")
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
    print("4")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as file:
                json_data = json.load(file)
                last_updated = datetime.fromisoformat(json_data['last_updated']).date()
                if last_updated == datetime.now().date():
                    print("5")
                    return json_data  
                else:
                    should_refresh = True
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print("❗ Cache file invalid or corrupted:", e)

    if should_refresh:
        latest = getheadlines() 
        from summarizermodel import summarize_news  
        if latest:
            newsdata = []
            print("6")
            for article in latest:
                desc = article.get("description") or article.get("content") or ""
                if len(desc) < 20: 
                    summary = desc
                else:
                    summary = summarize_news(desc)
                impacts=getimpact(article["title"],summary)
                print("7")
                sentiment=impacttosentiment(impacts)
                print("8")
                reaction,action = sentiment_to_market_action(sentiment)
                print("9")
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
print("10")
print(get_news())