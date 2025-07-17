from flask_sqlalchemy import SQLAlchemy
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

    portfolios=db.relationship('portfolio', backref='users',cascade="all, delete")

class Portfolio(db.Model):
    __tablename__='portfolio'
    portfolioid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    userid=db.Column(db.Integer,db.ForeignKey('users.userid'))
    stockname=db.Column(db.String(100))
    companyname=db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    initialinvestment = db.Column(db.Numeric(12, 2))
    buy_date = db.Column(db.Date)