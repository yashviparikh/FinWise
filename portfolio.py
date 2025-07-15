import yfinance as yf
import requests
import certifi
# old_get = requests.get
# def safe_get(*args, **kwargs):
#     kwargs['verify'] = certifi.where()
#     return old_get(*args, **kwargs)
# requests.get = safe_get

def getfromapi(stockname):
    name=yf.Ticker(stockname)
    info=name.info
    print("ltp",info["regularMarketPrice"])
    ltp=info["regularMarketPrice"]
    return(ltp)
    #print("daily change",info["regularMarketChange"])
    #print("change percentage",info["regularMarketChangePercent"])
#getfromapi("RELIANCE.NS")

def calc(qty,buyprice,name):
    loss,losspercent,profit,profitpercent=0,0,0,0
    ltp=getfromapi(name)
    #total invested=qty*buyprice
    totalinvested=qty*buyprice
    if(ltp<buyprice):
        loss=buyprice-ltp
        losspercent=loss/(ltp+buyprice)*100
    else:
        profit=ltp-buyprice
        profitpercent=profit/(ltp+buyprice)*100
    return{
        "ltp":ltp,
        "totalinvested":totalinvested,
        "loss":loss,
        "losspercent":losspercent,
        "profit":profit,
        "profitpercent":profitpercent
    }
print(calc(100,200,"RELIANCE.NS"))
#to display- no. of shares invested,total value invested,ltp,profit,profitper,loss,losspercent