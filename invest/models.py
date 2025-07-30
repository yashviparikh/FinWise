from invest import db
from datetime import datetime 

class Users(db.Model):
    __tablename__='users'
    userid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    money=db.Column(db.Numeric(12,2), default=10000)
    profitorloss=db.Column(db.Numeric(12,2), default=0)
    profitpercent=db.Column(db.Float,default=0.0)
    losspercent=db.Column(db.Float,default=0.0)
    last_login=db.Column(db.DateTime)
    progress = db.Column(db.Integer,default=0)
    level = db.Column(db.Integer,default=0)

    watchlist = db.relationship('Watchlist', backref='users', lazy=True)
    portfolio =db.relationship('Portfolio', backref='users',cascade="all, delete")

class Stock(db.Model):
    __tablename__ = 'stock'
    stock_id = db.Column(db.Integer, primary_key=True)
    stock_symbol = db.Column(db.String(10), unique=True, nullable=False)
    stock_name = db.Column(db.String(100))

    watchlisted_by = db.relationship('Watchlist', backref='stock', lazy=True)
    portfolio_entries = db.relationship('Portfolio', backref='stock', lazy=True)


class Watchlist(db.Model): 
    __tablename__ = 'watchlist'
    watchlist_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.stock_id'), nullable=False)


class Portfolio(db.Model):
    __tablename__='portfolio'
    portfolioid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    userid=db.Column(db.Integer,db.ForeignKey('users.userid'))
    stockname=db.Column(db.String(100))
    companyname=db.Column(db.String(100))
    totalquantity = db.Column(db.Integer, default=0)  
    averagebuyprice = db.Column(db.Numeric(12, 2), default=0.00)  
    totalinvested = db.Column(db.Numeric(12, 2), default=0.00)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.stock_id')) 

class Transactionhistory(db.Model):
    __tablename__='transactionhistory'
    transactionid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    userid=db.Column(db.Integer,db.ForeignKey('users.userid'),nullable=False)
    portfolioid=db.Column(db.Integer,db.ForeignKey('portfolio.portfolioid'),nullable=False)
    companyname=db.Column(db.String(100),nullable=False)
    stockname=db.Column(db.String(100),nullable=False)
    quantity=db.Column(db.Integer,nullable=False)
    price=db.Column(db.Numeric(12,2),nullable=False)
    transactiontype=db.Column(db.String(10),nullable=False)
    timestamp=db.Column(db.DateTime,default=datetime)


class FIFOLot(db.Model):
    __tablename__ = 'fifolot'
    lotid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    portfolioid = db.Column(db.Integer, db.ForeignKey('portfolio.portfolioid'), nullable=False)
    companyname = db.Column(db.String(100), nullable=False)
    quantityremaining = db.Column(db.Integer, nullable=False)  
    pricepershare = db.Column(db.Numeric(12, 2), nullable=False) 
    buydate = db.Column(db.DateTime, default=datetime)





