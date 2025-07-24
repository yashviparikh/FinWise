import yfinance as yf
import requests
import certifi
from dbmodel import db,Portfolio,Transactionhistory,User,FIFOLot
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

def calc(buyprice,qty,name):
    if qty==0:
        return{
        "name":name,
        "ltp":ltp,
        "profitorloss":0,
        "percentage":0
    }
    profitorloss=0
    percentage=0
    ltp=getfromapi(name)
    if ltp is None:
        return {"error": f"LTP not available for {name}"}
    boughtvalue=buyprice*qty
    nowvalue=ltp*qty
    profitorloss = nowvalue - boughtvalue
    percentage = (profitorloss / boughtvalue) * 100
    return{
        "name":name,
        "ltp":ltp,
        "profitorloss":profitorloss,
        "percentage":percentage,
        "boughtvalue":boughtvalue,
        "nowvalue":nowvalue
    }
#print(calc(buyprice=10,qty=20,name="DAVANGERE.NS"))
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
        stocksummary=calc(buyprice=averagebuyprice,qty=totalquantity,name=stockname)
        portfolio.append(stocksummary)
    #print(portfolio)
# for each company in portfolio get stockname,companyname,total quantity,average buy price,total invested from db function
#call calc function with totalqty,stockname to get ltp,loss/profit,percent

def buy(userid,stockname,qty,price,companyname):
    usermoney=usercheck(userid)["money"]
    if Decimal(usermoney) > 0 and Decimal(usermoney) >= Decimal(qty) * Decimal(price):
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
            portfolioid=new_entry.portfolioid


        user = userfromdb(userid)
        user.money = Decimal(user.money) - Decimal(qty) * Decimal(price)
        db.session.add(user)
        db.session.commit()


        fifo_buy(userid=userid,
         portfolioid=portfolioid,
         companyname=companyname,
         qty=qty,
         price=Decimal(price),
         date=datetime.now())
            
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
            return
        totalquantity=previousqty-qty
        totalinvested = previoustotalinvested - Decimal(qty) * Decimal(price)
        averagebuyprice = totalinvested / totalquantity if totalquantity else Decimal(0)
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

        fifo_sell(userid=userid,
          portfolioid=portfolioid,
          companyname=companyname,
          sellqty=qty,
          sellprice=Decimal(price))

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

def fifo_buy(userid, portfolioid, companyname, qty, price, date):
    new_lot = FIFOLot(
        userid=userid,
        portfolioid=portfolioid,
        companyname=companyname,
        quantityremaining=qty,
        pricepershare=price,
        buydate=date
    )
    db.session.add(new_lot)
    db.session.commit()

def fifo_sell(userid, portfolioid, companyname, sellqty, sellprice):
    lots = FIFOLot.query.filter_by(userid=userid, portfolioid=portfolioid, companyname=companyname)\
                        .order_by(FIFOLot.buydate.asc()).all()

    remainingqty = sellqty

    for lot in lots:
        if remainingqty == 0:
            break

        if lot.quantityremaining <= remainingqty:
            remainingqty -= lot.quantityremaining
            db.session.delete(lot)
        else:
            lot.quantityremaining -= remainingqty
            remainingqty = 0
            db.session.add(lot)

    if remainingqty > 0:
        print(f"[ERROR] Not enough shares in FIFO lots to sell {sellqty} shares.")
        raise ValueError("Insufficient quantity in FIFO lots.")
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        #gettingfromdb(1)
        #buy(userid=1,stockname="TCS.NS",qty=6,price=getfromapi(stockname="TCS.NS"),companyname="TCS")
        #print(usercheck())
        # print("----- Starting FIFO Test -----")

        # # 1. Buy 10 shares at price 100
        # buy(userid=1, stockname="TCS.NS", qty=10, price=100, companyname="TCS")

        # # 2. Buy 5 shares at price 120
        # buy(userid=1, stockname="TCS.NS", qty=5, price=120, companyname="TCS")

        # # 3. Sell 12 shares (should use 10 from first lot and 2 from second)
        # sell(userid=1, stockname="TCS.NS", qty=12, price=130, companyname="TCS")

        # # 4. Check remaining FIFO lots
        # lots = FIFOLot.query.filter_by(userid=1).all()
        # for lot in lots:
        #     print(f"LotID {lot.lotid} | Qty Remaining: {lot.quantityremaining} | Price: {lot.pricepershare} | BuyDate: {lot.buydate}")

        # # 5. Check updated portfolio
        # fromdb = get_stock_entry(1, "TCS.NS")
        # print(f"\nPortfolio - Qty: {fromdb.totalquantity} | Invested: {fromdb.totalinvested} | Avg Price: {fromdb.averagebuyprice}")

        # # 6. Check transaction history
        # transactions = Transactionhistory.query.filter_by(userid=1).all()
        # for t in transactions:
        #     print(f"{t.transactiontype.upper()} | Qty: {t.quantity} | Price: {t.price} | Time: {t.timestamp}")

        # # 7. Check user money
        # user = userfromdb(1)
        # print(f"\nUser Balance: ₹{user.money}")
        pass
