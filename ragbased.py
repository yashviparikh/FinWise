import string
import os
import json
def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text.strip()


def getimpact(headline,summary):
    cache_path='kb.json'
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as file:
                kb = json.load(file)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print("❗ Cache file invalid or corrupted:", e)
    combined=headline+" "+summary
    normalized=normalize(combined)
    #print(normalized)

    results = []
    for keyword, impact in kb.items():
        if keyword in normalized:   
            results.append(impact)  
    unique_results = list(dict.fromkeys(results))

    if not results:
        impacts = {"impact": "no clear impact detected"}
    else:
        impacts = unique_results

    return impacts


headline="US stocks mixed as Dow sinks, S&P 500 nears record, Nasdaq rides AI boom - Nvidia earnings jolt but GDP growth surprises Wall street"
summary="U.S. stock market movements on 28 August 2025 as Nvidia earnings shake tech stocks . Get insights on GDP growth, inflation trends, and market implications for investors navigating volatility ."
print(getimpact(headline,summary))
