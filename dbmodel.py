from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db=SQLAlchemy()

class User(db.Model):
    __tablename__='users'
    userid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    name=db.Column(db.String(100),nullable=False)
    money=db.Column(db.Numeric(12,2), default=10000)
    profit=db.Column(db.Numeric(12,2), default=0)
    loss=db.Column(db.Numeric(12,2), default=0)
    profitpercent=db.Column(db.Float,default=0.0)
    losspercent=db.Column(db.Float,default=0.0)
    last_login=db.Column(db.DateTime)
    progress = db.Column(db.Integer,default=0)
    level = db.Column(db.Integer,default=0)

    portfolios=db.relationship('Portfolio', backref='users',cascade="all, delete")

class Portfolio(db.Model):
    __tablename__='portfolio'
    portfolioid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    userid=db.Column(db.Integer,db.ForeignKey('users.userid'))
    stockname=db.Column(db.String(100))
    companyname=db.Column(db.String(100))
    totalquantity = db.Column(db.Integer, default=0)  
    averagebuyprice = db.Column(db.Numeric(12, 2), default=0.00)  
    totalinvested = db.Column(db.Numeric(12, 2), default=0.00)

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
    timestamp=db.Column(db.DateTime,default=datetime.utcnow)

class FIFOLot(db.Model):
    __tablename__ = 'fifolot'
    lotid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('users.userid'), nullable=False)
    portfolioid = db.Column(db.Integer, db.ForeignKey('portfolio.portfolioid'), nullable=False)
    companyname = db.Column(db.String(100), nullable=False)
    quantityremaining = db.Column(db.Integer, nullable=False)  
    pricepershare = db.Column(db.Numeric(12, 2), nullable=False) 
    buydate = db.Column(db.DateTime, default=datetime)
