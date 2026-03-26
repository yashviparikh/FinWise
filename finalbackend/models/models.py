from sqlalchemy import Column, Integer, String, Float, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    userid = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255))
    otp_code = Column(String(10))
    otp_ts = Column(DateTime)
    money = Column(Numeric(12, 2), default=10000)
    profitorloss = Column(Numeric(12, 2), default=0)
    profitpercent = Column(Float, default=0.0)
    losspercent = Column(Float, default=0.0)
    last_login = Column(DateTime)
    progress = Column(Integer, default=0)
    level = Column(Integer, default=0)

    watchlist = relationship('Watchlist', back_populates='user', cascade="all, delete-orphan")
    portfolio = relationship('Portfolio', back_populates='user', cascade="all, delete-orphan")

class Stock(Base):
    __tablename__ = 'stock'
    stock_id = Column(Integer, primary_key=True)
    stock_symbol = Column(String(10), unique=True, nullable=False)
    stock_name = Column(String(100))

    watchlisted_by = relationship('Watchlist', back_populates='stock', cascade="all, delete-orphan")
    portfolio_entries = relationship('Portfolio', back_populates='stock', cascade="all, delete-orphan")

class Watchlist(Base):
    __tablename__ = 'watchlist'
    watchlist_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.userid'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stock.stock_id'), nullable=False)

    user = relationship('Users', back_populates='watchlist')
    stock = relationship('Stock', back_populates='watchlisted_by')

class Portfolio(Base):
    __tablename__ = 'portfolio'
    portfolioid = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('users.userid'))
    stockname = Column(String(100))
    companyname = Column(String(100))
    totalquantity = Column(Integer, default=0)
    averagebuyprice = Column(Numeric(12, 2), default=0.00)
    totalinvested = Column(Numeric(12, 2), default=0.00)
    stock_id = Column(Integer, ForeignKey('stock.stock_id'))
    sector = Column(String(100), nullable=True)

    user = relationship('Users', back_populates='portfolio')
    stock = relationship('Stock', back_populates='portfolio_entries')

class Transactionhistory(Base):
    __tablename__ = 'transactionhistory'
    transactionid = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('users.userid'), nullable=False)
    portfolioid = Column(Integer, ForeignKey('portfolio.portfolioid'), nullable=False)

class FIFOLot(Base):
    __tablename__ = 'fifolot'
    lotid = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('users.userid'), nullable=False)
    portfolioid = Column(Integer, ForeignKey('portfolio.portfolioid'), nullable=False)
    companyname = Column(String(100), nullable=False)
    quantityremaining = Column(Integer, nullable=False)
    pricepershare = Column(Numeric(12, 2), nullable=False)
    buydate = Column(DateTime, default=datetime.utcnow)

class Stockhistory(Base):
    __tablename__ = 'stockhistory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('users.userid'))
    stock_name = Column(String(50), nullable=False)
    dates = Column(Date, nullable=False)
    close_price = Column(Float, nullable=False)

class Useractivity(Base):
    __tablename__ = 'useractivity'
    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('users.userid'))
    activity_type = Column(String(50), nullable=False)
    activity_value = Column(Float, default=0)
    activity_date = Column(DateTime, default=datetime.utcnow)

class Stockdata(Base):
    __tablename__ = 'stockdata'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(30))
    date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(Integer)

class Milestones(Base):
    __tablename__ = 'milestones'
    milestone_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    description = Column(String(255))
    type = Column(String(20))
    threshold_value = Column(Float)

class UserMilestones(Base):
    __tablename__ = 'usermilestones'
    usermilestone_id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, ForeignKey('users.userid'))
    milestone_id = Column(Integer, ForeignKey('milestones.milestone_id'))
    achieved_on = Column(DateTime, default=datetime.utcnow)
