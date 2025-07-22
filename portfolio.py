import yfinance as yf
import requests
import certifi
from dbmodel import db,Portfolio 
from app import app
from datetime import datetime
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

def calc(qty,name):
    if qty==0:
        return 0,0
    loss,losspercent,profit,profitpercent=0,0,0,0
    ltp=getfromapi(name)
    if ltp is None:
        return {"error": f"LTP not available for {name}"}
    nowvalue=ltp*qty
    if(ltp<nowvalue):
        loss=ltp-nowvalue
        losspercent=loss/(nowvalue-ltp)*100
    else:
        profit=nowvalue-ltp
        profitpercent=profit/(nowvalue-ltp)*100
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
        portfolio.append({stockname,companyname,totalquantity,averagebuyprice,totalinvested})
        stocksummary=calc(totalquantity,stockname)
        portfolio.append(stocksummary)
    #print(portfolio)
# for each company in portfolio get stockname,companyname,total quantity,average buy price,total invested from db function
#call calc function with totalqty,stockname to get ltp,loss/profit,percent

def buy(userid,name,qty,price,companyname):
    fromdb=get_stock_entry(1,"reliance.ns")
    if fromdb:
        previousqty=fromdb.totalquantity
        previoustotalinvested=fromdb.totalinvested
        totalquantity=qty+previousqty
        totalinvested=previoustotalinvested+(qty*price)
        averagebuyprice=totalinvested/totalquantity
        fromdb.totalquantity=totalquantity
        fromdb.totalinvested=totalinvested
        fromdb.averagebuyprice=averagebuyprice
    else:
        totalinvested=qty*price
        averagebuyprice=price
        
    new_entry = Portfolio(
            userid=userid,
            stockname=name,
            companyname=companyname,
            totalquantity=qty,
            totalinvested=totalinvested,
            averagebuyprice=averagebuyprice
        )
    newtransactionentry=Transactionhistory(
        userid=userid,
        stockname=name,
        companyname=companyname,
        quantity=qty,
        price=price,
        transactiontype="buy",
        timestamp=datetime.now()
    )
    db.session.add(new_entry)
    db.session.add(newtransactionentry)
    db.session.commit()
    print("updateddb")
def get_stock_entry(userid, stockname):
    return Portfolio.query.filter_by(userid=userid, stockname=stockname).first()

def sell(userid,stockname,companyname,qty,price):
    fromdb=get_stock_entry(userid,stockname)
    if fromdb:
        previousqty=fromdb.totalquantity
        previoustotalinvested=fromdb.totalinvested
        if previousqty==0:
            print("cannot sell what you dont own")
        totalquantity=previousqty-qty
        totalinvested=previoustotalinvested-(qty*price)
        averagebuyprice=totalinvested/totalquantity
        fromdb.totalquantity=totalquantity
        fromdb.totalinvested=totalinvested
        fromdb.averagebuyprice=averagebuyprice
           
    else:
        print("cant sell what you dont own")
    new_entry = Portfolio(
            userid=userid,
            stockname=stockname,
            companyname=companyname,
            totalquantity=qty,
            totalinvested=totalinvested,
            averagebuyprice=averagebuyprice
        )
    newtransactionentry=Transactionhistory(
        userid=userid,
        stockname=stockname,
        companyname=companyname,
        quantity=qty,
        price=price,
        transactiontype="buy",
        timestamp=datetime.now()
    )
    db.session.add(new_entry)
    db.session.add(newtransactionentry)
    db.session.commit()
    print("updateddb")
if __name__ == '__main__':
    with app.app_context():
        #gettingfromdb(1)
        #buy(1,"RELIANCE.NS",3,300,"reliance")
