import yfinance as yf
import requests
import certifi
from dbmodel import db,Portfolio 
from app import app
old_get = requests.get
def safe_get(*args, **kwargs):
     kwargs['verify'] = certifi.where()
     return old_get(*args, **kwargs)
requests.get = safe_get

#print("portfolio called")

def getfromapi(stockname):
    name=yf.Ticker(stockname)
    info=name.info
    if "regularMarketPrice" in info:
        ltp = info["regularMarketPrice"]
        #print(f"ltp for {name}: {ltp}")
        return ltp
    else:
        print(f"[ERROR] regularMarketPrice not found for {name}")
        print(f"Available keys: {list(info.keys())}")
        return None
getfromapi("RELIANCE.NS")

def calc(qty,averagebuyprice,name):
    if qty==0:
        return 0,0
    loss,losspercent,profit,profitpercent=0,0,0,0
    ltp=getfromapi(name)
    if ltp is None:
        return {"error": f"LTP not available for {name}"}
    averagebuyprice=float(averagebuyprice)
    if(ltp<averagebuyprice):
        loss=averagebuyprice-ltp
        losspercent=loss/(ltp+averagebuyprice)*100
    else:
        profit=ltp-averagebuyprice
        profitpercent=profit/(ltp+averagebuyprice)*100
    return{
        "name":name,
        "ltp":ltp,
        "loss":loss,
        "losspercent":losspercent,
        "profit":profit,
        "profitpercent":profitpercent,
    }
#print(calc(100,200,"RELIANCE.NS"))
#to display- no. of shares invested,total value invested,ltp,profit,profitper,loss,losspercent

def gettingfromdb(userid):
    userinfo=Portfolio.query.filter_by(userid=userid).all()
    portfolio=[]
    for i in userinfo:
        portfolioid=i.portfolioid
        userid=i.userid
        stockname=i.stockname
        companyname=i.companyname
        totalquantity=i.totalquantity
        averagebuyprice=i.averagebuyprice
        totalinvested=i.totalinvested
        stocksummary=calc(totalquantity,averagebuyprice,stockname)
        portfolio.append(stocksummary)
    print(portfolio)

if __name__ == '__main__':
    with app.app_context():
        gettingfromdb(1)
