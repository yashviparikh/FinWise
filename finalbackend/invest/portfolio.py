import yfinance as yf
import requests
import certifi
import pandas as pd
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm.exc import NoResultFound
import concurrent.futures
import time
# Import all necessary models
from invest.models import (
    Users, Portfolio, Transactionhistory, FIFOLot,
    Useractivity, Stockhistory, Stockdata, Milestones, UserMilestones, db
)
# ---------------- LTP Cache ----------------
LTP_CACHE = {}
CACHE_TTL = 300  # seconds

def _get_live_price_for_symbol(symbol_plain):
    """Fetch live price with in-memory caching"""
    symbol_plain = symbol_plain.upper()
    now = time.time()

    # 1️⃣ Check cache
    cached = LTP_CACHE.get(symbol_plain)
    if cached and (now - cached["timestamp"] < CACHE_TTL):
        return cached["price"], cached["change"], cached["change_percent"]

    # 2️⃣ Fetch from yfinance
    try:
        ticker_symbol = f"{symbol_plain}.NS"
        t = yf.Ticker(ticker_symbol)
        info = t.info or {}

        price = info.get("regularMarketPrice") or info.get("previousClose")
        prev = info.get("previousClose")

        if price is None:
            return None, None, None

        change = round(float(price) - float(prev), 2) if prev else 0
        change_percent = round((change / float(prev)) * 100, 2) if prev and prev != 0 else 0

        # 3️⃣ Store in cache
        LTP_CACHE[symbol_plain] = {
            "price": round(float(price), 2),
            "change": change,
            "change_percent": change_percent,
            "timestamp": now,
        }

        return round(float(price), 2), change, change_percent

    except Exception:
        return None, None, None

# ---------------- Parallel LTP Fetch ----------------
def fetch_ltp_parallel(symbols):
    """Fetch multiple LTPs concurrently"""
    results = []

    def fetch(symbol):
        price, change, change_percent = _get_live_price_for_symbol(symbol)
        return {
            "stockname": symbol,
            "price": price,
            "change": change,
            "change_percent": change_percent
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_sym = {executor.submit(fetch, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            res = future.result()
            results.append(res)

    return pd.DataFrame(results)
# --- Fix SSL issues for yfinance if needed ---
old_get = requests.get
def safe_get(*args, **kwargs):
    kwargs["verify"] = certifi.where()
    return old_get(*args, **kwargs)
requests.get = safe_get

# ---------------- Utils ----------------
SECTOR_DICT = {}
def preload_sectors():
    symbols = [s.stockname.upper() for s in Stockdata.query.all()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_sym = {executor.submit(fetch_sector, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym, sector = future.result()
            SECTOR_DICT[sym] = sector

def fetch_sector(symbol):
    """Fetch sector from yfinance once"""
    try:
        ticker_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        info = yf.Ticker(ticker_symbol).info
        sector = info.get("sector") or "Other"
        return symbol, sector
    except Exception:
        return symbol, "Other"

def get_sector(symbol):
    """Get sector from preloaded dictionary"""
    return SECTOR_DICT.get(symbol.upper(), "Other")

def gettingfromdb(userid):
    """Fetch holdings and enrich with live data & P&L."""
    rows = Portfolio.query.filter_by(userid=userid).all()
    if not rows:
        return []

    # 1️⃣ Prepare stock symbols
    symbols = [r.stockname for r in rows]

    # 2️⃣ Fetch LTPs concurrently using the cached function
    ltp_results = {}
    def fetch_ltp(stockname):
        price, _, _ = _get_live_price_for_symbol(stockname)
        return stockname, price

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_stock = {executor.submit(fetch_ltp, s): s for s in symbols}
        for future in concurrent.futures.as_completed(future_to_stock):
            stock, price = future.result()
            ltp_results[stock] = price
    processed = []
    for r in rows:
        ltp = ltp_results.get(r.stockname) or float(r.averagebuyprice or 0)
        total_quantity = r.totalquantity or 0
        total_invested = float(r.totalinvested or 0)
        now_value = ltp * total_quantity
        pnl = now_value - total_invested
        pct = (pnl / total_invested * 100) if total_invested > 0 else 0
        processed.append({
            "portfolioid": r.portfolioid,
            "stockname": r.stockname,
            "companyname": r.companyname,
            "totalquantity": total_quantity,
            "averagebuyprice": float(r.averagebuyprice or 0),
            "totalinvested": total_invested,
            "ltp": ltp,
            "profitorloss": pnl,
            "percentage": pct,
            "nowvalue": now_value
        })
    return processed


def get_stock_entry(userid, stockname):
    return Portfolio.query.filter_by(userid=userid, stockname=stockname).first()


def userfromdb(userid):
    try:
        return Users.query.filter_by(userid=userid).one()
    except NoResultFound:
        return None

# ---------------- Buy / Sell Logic ----------------

def buy(userid, stockname, qty, price, companyname):
    user = userfromdb(userid)
    if not user:
        raise ValueError("User not found")

    total_cost = Decimal(qty) * Decimal(price)
    if Decimal(user.money) < total_cost:
        raise ValueError("Insufficient funds")

    fromdb = get_stock_entry(userid, stockname)
    if fromdb:
        fromdb.totalquantity += qty
        fromdb.totalinvested = Decimal(fromdb.totalinvested or 0) + total_cost
        fromdb.averagebuyprice = fromdb.totalinvested / fromdb.totalquantity
        portfolioid = fromdb.portfolioid
    else:
        new_entry = Portfolio(
            userid=userid,
            stockname=stockname,
            companyname=companyname,
            totalquantity=qty,
            totalinvested=total_cost,
            averagebuyprice=Decimal(price)
        )
        db.session.add(new_entry)
        db.session.flush()
        portfolioid = new_entry.portfolioid

    user.money = Decimal(user.money) - total_cost
    db.session.add(user)

    fifo_buy(userid, portfolioid, companyname, qty, Decimal(price), datetime.now())
    db.session.add(Transactionhistory(
        portfolioid=portfolioid, userid=userid,
        stockname=stockname, companyname=companyname,
        quantity=qty, price=price, transactiontype="buy", timestamp=datetime.now()
    ))
    db.session.add(Useractivity(userid=userid, activity_type="buy", activity_value=float(total_cost)))
    db.session.commit()
    return {"status": "ok", "action": "buy", "qty": qty, "stock": stockname}


def sell(userid, stockname, companyname, qty, price):
    fromdb = get_stock_entry(userid, stockname)
    if not fromdb or qty > fromdb.totalquantity:
        raise ValueError("Not enough shares to sell")

    fifo_cost = fifo_sell(userid, fromdb.portfolioid, companyname, qty, Decimal(price))
    
    fromdb.totalquantity -= qty
    fromdb.totalinvested = Decimal(fromdb.totalinvested or 0) - fifo_cost
    
    if fromdb.totalquantity > 0:
        fromdb.averagebuyprice = fromdb.totalinvested / fromdb.totalquantity
    else:
        # If all shares are sold, reset to 0 to avoid precision issues
        fromdb.averagebuyprice = Decimal(0)
        fromdb.totalinvested = Decimal(0)

    user = userfromdb(userid)
    user.money = Decimal(user.money) + (Decimal(qty) * Decimal(price))
    db.session.add(user)
    
    db.session.add(Transactionhistory(
        portfolioid=fromdb.portfolioid, userid=userid,
        stockname=stockname, companyname=companyname,
        quantity=qty, price=price, transactiontype="sell", timestamp=datetime.now()
    ))
    db.session.add(Useractivity(userid=userid, activity_type="sell", activity_value=float(qty * price)))
    db.session.commit()
    return {"status": "ok", "action": "sell", "qty": qty, "stock": stockname}


# ---------------- FIFO Logic ----------------

def fifo_buy(userid, portfolioid, companyname, qty, price, date):
    lot = FIFOLot(userid=userid, portfolioid=portfolioid, companyname=companyname,
                  quantityremaining=qty, pricepershare=price, buydate=date)
    db.session.add(lot)


def fifo_sell(userid, portfolioid, companyname, sellqty, sellprice):
    lots = FIFOLot.query.filter_by(
        userid=userid, 
        portfolioid=portfolioid, 
        companyname=companyname
    ).order_by(FIFOLot.buydate.asc()).all()
    
    remaining_to_sell = sellqty
    total_cost_of_sold_shares = Decimal(0)

    for lot in lots:
        if remaining_to_sell == 0:
            break
            
        if lot.quantityremaining <= remaining_to_sell:
            sold_from_lot = lot.quantityremaining
            total_cost_of_sold_shares += Decimal(sold_from_lot) * Decimal(lot.pricepershare)
            remaining_to_sell -= sold_from_lot
            db.session.delete(lot)
        else:
            sold_from_lot = remaining_to_sell
            total_cost_of_sold_shares += Decimal(sold_from_lot) * Decimal(lot.pricepershare)
            lot.quantityremaining -= sold_from_lot
            db.session.add(lot)
            remaining_to_sell = 0

    if remaining_to_sell > 0:
        db.session.rollback()
        raise ValueError("FIFO logic error: Insufficient quantity in FIFO lots to sell.")

    return total_cost_of_sold_shares


# ---------------- Dashboard Metrics Calculation ------------------

def calculate_user_metrics(userid):
    user = Users.query.get(userid)
    if not user:
        return {"error": "User not found"}

    # 1. Progress & Level
    total_investment = sum(p.totalinvested for p in Portfolio.query.filter_by(userid=userid).all())
    holdings = gettingfromdb(userid)
    current_value = sum(h['nowvalue'] for h in holdings)
    total_pnl = current_value - float(total_investment)
    
    profit_percent = (total_pnl / float(total_investment) * 100) if total_investment > 0 else 0
    profit_score = min(max(profit_percent, 0), 100) * 0.5

    total_trades = Transactionhistory.query.filter_by(userid=userid).count()
    trade_score = min(total_trades / 20, 1) * 30

    num_stocks = Portfolio.query.filter_by(userid=userid).filter(Portfolio.totalquantity > 0).count()
    diversification_score = min(num_stocks / 10, 1) * 20

    total_score = profit_score + trade_score + diversification_score
    total_score = min(total_score, 100)

    if total_score < 40: level = "Beginner"
    elif total_score < 70: level = "Intermediate"
    else: level = "Advanced"
    user.level = level

    # 2. Consistency (login streak)
    today = datetime.today().date()
    streak = 0
    logins = Useractivity.query.filter_by(userid=userid, activity_type='login').order_by(Useractivity.activity_date.desc()).all()
    
    if logins:
        unique_login_dates = sorted(list(set(l.activity_date.date() for l in logins)), reverse=True)
        if unique_login_dates[0] == today:
            streak = 1
            for i in range(len(unique_login_dates) - 1):
                if unique_login_dates[i] - timedelta(days=1) == unique_login_dates[i+1]:
                    streak += 1
                else:
                    break
    
    db.session.commit()

    return {
        "progress_score": round(total_score, 2),
        "level": level,
        "login_streak": streak,
    }


# ---------------- Main Dashboard Data Aggregator ------------------

from flask import Response
import csv
import io

def get_dashboard_data(userid):
    """Unify portfolio + analytics for dashboard, with sector info for pie chart."""
    user = userfromdb(userid)
    if not user:
        return {"error": "User not found"}

    wallet = float(user.money) if user.money else 0.0
    portfolio = gettingfromdb(userid)
    metrics = calculate_user_metrics(userid)

    # ✅ Add sector dynamically for each holding
    investment_split = [
        {
            "company": h["companyname"],
            "stockname": h["stockname"],
            "sector": get_sector(h["stockname"]),
            "amount": h["nowvalue"]
        }
        for h in portfolio if h["nowvalue"] > 0
    ]

    history = Stockhistory.query.filter_by(userid=userid).order_by(Stockhistory.dates.asc()).all()
    portfolio_value_trend, profit_loss_trend = [], []
    if history:
        df = pd.DataFrame([{"date": h.dates, "stock": h.stock_name, "close": h.close_price} for h in history])
        if not df.empty:
            daily_portfolio_value = df.groupby("date")["close"].sum().reset_index()
            daily_portfolio_value["date"] = pd.to_datetime(daily_portfolio_value["date"])
            
            monthly_summary = daily_portfolio_value.set_index('date').resample('M').last().reset_index()
            monthly_summary["month"] = monthly_summary["date"].dt.strftime("%b")

            portfolio_value_trend = [{"date": row["month"], "value": float(row["close"])} for _, row in monthly_summary.iterrows()]
            base_val = daily_portfolio_value["close"].iloc[0] if not daily_portfolio_value.empty else 0
            profit_loss_trend = [{"date": row["month"], "profit_loss": float(row["close"] - base_val)} for _, row in monthly_summary.iterrows()]

    transactions = [{
        "type": t.transactiontype,
        "stockname": t.stockname,
        "price": float(t.price),
        "date": str(t.timestamp.strftime('%Y-%m-%d %H:%M'))
    } for t in Transactionhistory.query.filter_by(userid=userid).order_by(Transactionhistory.timestamp.desc()).limit(5)]

    return {
        "wallet": wallet,
        "portfolio": portfolio,
        "metrics": metrics,
        "investment_split": investment_split,   # ✅ now includes sector
        "portfolio_value_trend": portfolio_value_trend,
        "profit_loss_trend": profit_loss_trend,
        "transactions": transactions
    }
