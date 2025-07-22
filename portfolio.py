import yfinance as yf
import requests
import certifi
from dbmodel import db,Portfolio,Transactionhistory,User
from app import app
from datetime import datetime
from decimal import Decimal
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
#print(getfromapi("TCS.NS"))

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

def buy(userid,stockname,qty,price,companyname):
    usermoney=usercheck(userid)["money"]
    if usermoney>0 and usermoney>(qty*price):
        fromdb=get_stock_entry(userid,stockname)
        if fromdb:
            previousqty=fromdb.totalquantity
            previoustotalinvested=fromdb.totalinvested
            totalquantity=qty+previousqty
            totalinvested = previoustotalinvested + (Decimal(qty) * Decimal(price))
            averagebuyprice = totalinvested / totalquantity if totalquantity else Decimal(0)
            fromdb.totalquantity=totalquantity
            fromdb.totalinvested=totalinvested
            fromdb.averagebuyprice=averagebuyprice

            db.session.add(fromdb)
            db.session.commit()
            portfolioid = fromdb.portfolioid
        else:
            totalinvested = Decimal(qty) * Decimal(price)
            averagebuyprice = Decimal(price)
            new_entry = Portfolio(
                userid=userid,
                stockname=stockname,
                companyname=companyname,
                totalquantity=qty,
                totalinvested=totalinvested,
                averagebuyprice=averagebuyprice
            )
            db.session.add(new_entry)
            db.session.commit()
            user = userfromdb(userid)
            user.money = Decimal(user.money) - Decimal(qty) * Decimal(price)
            db.session.add(user)
            db.session.commit()

            portfolioid=new_entry.portfolioid

        newtransactionentry=Transactionhistory(
            portfolioid=portfolioid,
            userid=userid,
            stockname=stockname,
            companyname=companyname,
            quantity=qty,
            price=price,
            transactiontype="buy",
            timestamp=datetime.now()
        )
        db.session.add(newtransactionentry)
        db.session.commit()
        print("updateddb")
    else:
        print("insufficient funds")

def get_stock_entry(userid, stockname):
    return Portfolio.query.filter_by(userid=userid, stockname=stockname).first()

def userfromdb(userid):
    return User.query.filter_by(userid=userid).one()

def usercheck(userid):
    user=userfromdb(userid)
    if user:
        return{
            "userid":user.userid,
            "money":user.money,
            "name":user.name,
            "profit": float(user.profit),
            "loss": float(user.loss),
            "profitpercent": user.profitpercent,
            "losspercent": user.losspercent,
            "last_login": user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else None,
            "progress": user.progress,
            "level": user.level
            }
    else:
        return {"error": "User not found"}

def sell(userid,stockname,companyname,qty,price):
    fromdb=get_stock_entry(userid,stockname)
    if fromdb:
        previousqty=fromdb.totalquantity
        previoustotalinvested=fromdb.totalinvested
        if qty>previousqty:
            print("cannot sell what you don't own")
        totalquantity=previousqty-qty
        totalinvested = previoustotalinvested - Decimal(qty) * Decimal(price)
        averagebuyprice = totalinvested / totalquantity if totalquantity else 0
        fromdb.totalquantity=totalquantity
        fromdb.totalinvested=totalinvested
        fromdb.averagebuyprice=averagebuyprice
        db.session.add(fromdb)
        db.session.commit()

        user = userfromdb(userid)
        user.money = Decimal(user.money) + Decimal(qty) * Decimal(price)
        db.session.add(user)
        db.session.commit()
        portfolioid = fromdb.portfolioid
    else:
        print("cant sell what you dont own")
        return
    newtransactionentry=Transactionhistory(
        portfolioid=portfolioid,
        userid=userid,
        stockname=stockname,
        companyname=companyname,
        quantity=qty,
        price=price,
        transactiontype="sell",
        timestamp=datetime.now()
    )
    db.session.add(newtransactionentry)
    db.session.commit()
    print("updateddb")
if __name__ == '__main__':
    with app.app_context():
        #gettingfromdb(1)
        buy(userid=1,stockname="TCS.NS",qty=6,price=getfromapi(stockname="TCS.NS"),companyname="TCS")
        #print(usercheck())