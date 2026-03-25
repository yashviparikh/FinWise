import string
import os
import json
def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text.strip()

BASE_DIR = os.path.dirname(__file__)  # directory where ragbased.py lives
KB_PATH = os.path.join(BASE_DIR, "kb.json")

with open(KB_PATH, "r") as f:
    KB = json.load(f)

def getimpact(headline, summary, kb=KB):
    combined = (headline + " " + summary).lower()
    results = [impact for k, impact in kb.items() if k in combined]
    return results if results else ["no clear impact detected"]

headline="Upcoming IPO: Mumbai-based SFC Environmental Tech files draft papers with Sebi to raise funds via public issue - Details"
summary=" Mumbai-based wastewater and solid waste treatment firm SFC Environmental Technologies is seeking to raise funds from the Indian stock market ."
#print(getimpact(headline,summary))

impact_to_sentiment = {
    "bullish": "bullish",
    "positive": "bullish",
    "possible undervaluation": "bullish",
    "may attract investors": "bullish",
    "bearish": "bearish",
    "fear": "bearish",
    "risk of correction": "bearish",
    "overbought risk": "bearish",
    "neutral": "neutral"
}

def impacttosentiment(impacts):
    score = {"bullish":0, "bearish":0, "neutral":0}
    for i in impacts:
        ilower=i.lower()
        if any(k in ilower for k in impact_to_sentiment.keys()):
            for k, s in impact_to_sentiment.items():
                if k in ilower:
                    score[s] += 1
        else:
            score["neutral"] += 1
    sentiment=max(score, key=score.get)
    return sentiment
#print(impacttosentiment())

sentiment_to_reaction = {
    "bullish": "Buying pressure",
    "bearish": "Selling pressure",
    "neutral": "Hold or sideways"
}
reaction_to_action = {
    "Buying pressure": "Consider increasing positions",
    "Selling pressure": "Consider reducing positions or hedging",
    "Hold or sideways": "Hold positions, monitor closely"
}
def sentiment_to_market_action(sentiment):
    reaction = sentiment_to_reaction.get(sentiment, "Hold or sideways")
    action = reaction_to_action.get(reaction, "Hold positions, monitor closely")
    return reaction, action
#print(sentiment_to_market_action(impacttosentiment()))