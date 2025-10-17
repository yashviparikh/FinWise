import yfinance as yf
import requests
import certifi
import pandas as pd
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm.exc import NoResultFound
import concurrent.futures
import time
from .models import (
    Users, Portfolio, Transactionhistory, FIFOLot,
    Useractivity, Stockhistory, Stockdata, Milestones, UserMilestones, db
)

# ---------------- LTP Cache ----------------
LTP_CACHE = {}
CACHE_TTL = 300  # seconds

def _get_live_price_for_symbol(symbol_plain):
    """Fetch live price with in-memory caching and correct symbol handling."""
    symbol_plain = symbol_plain.upper()
    now = time.time()

    cached = LTP_CACHE.get(symbol_plain)
    if cached and (now - cached["timestamp"] < CACHE_TTL):
        return cached["price"], cached["change"], cached["change_percent"]

    try:
        if not symbol_plain.endswith('.NS'):
            ticker_symbol = f"{symbol_plain}.NS"
        else:
            ticker_symbol = symbol_plain
            
        t = yf.Ticker(ticker_symbol)
        info = t.info or {}

        price = info.get("regularMarketPrice") or info.get("previousClose")
        prev = info.get("previousClose")

        if price is None:
            return None, None, None

        change = round(float(price) - float(prev), 2) if prev else 0
        change_percent = round((change / float(prev)) * 100, 2) if prev and prev != 0 else 0

        LTP_CACHE[symbol_plain] = {
            "price": round(float(price), 2),
            "change": change,
            "change_percent": change_percent,
            "timestamp": now,
        }
        return round(float(price), 2), change, change_percent
    except Exception:
        return None, None, None

def fetch_ltp_parallel(symbols):
    """Fetch multiple LTPs concurrently"""
    results = []
    def fetch(symbol):
        price, change, change_percent = _get_live_price_for_symbol(symbol)
        return {"stockname": symbol, "price": price, "change": change, "change_percent": change_percent}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_sym = {executor.submit(fetch, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            results.append(future.result())
    return pd.DataFrame(results)

# ---------------- Utils ----------------
def get_sector_from_api(symbol):
    """Fetches the sector for a given stock symbol from yfinance."""
    try:
        if not symbol.endswith('.NS'):
            ticker_symbol = f"{symbol}.NS"
        else:
            ticker_symbol = symbol
        info = yf.Ticker(ticker_symbol).info or {}
        return info.get("sector", "Other")
    except Exception:
        return "Other"

def gettingfromdb(userid):
    """Fetch holdings, enrich with live data & P&L, AND include the sector."""
    rows = Portfolio.query.filter_by(userid=userid).all()
    if not rows:
        return []

    symbols = [r.stockname for r in rows]
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
            "sector": r.sector or "Other",
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

# ---------------- Buy / Sell Logic (WITH FIXES) ----------------

def buy(userid, stockname, qty, price, companyname):
    user = userfromdb(userid)
    if not user: raise ValueError("User not found")

    total_cost = Decimal(qty) * Decimal(price)
    if Decimal(user.money) < total_cost: raise ValueError("Insufficient funds")

    fromdb = get_stock_entry(userid, stockname)
    if fromdb:
        fromdb.totalquantity += qty
        fromdb.totalinvested = Decimal(fromdb.totalinvested or 0) + total_cost
        fromdb.averagebuyprice = fromdb.totalinvested / fromdb.totalquantity
        portfolioid = fromdb.portfolioid
        if not fromdb.sector or fromdb.sector == 'Other':
            fromdb.sector = get_sector_from_api(stockname)
    else:
        stock_sector = get_sector_from_api(stockname)
        new_entry = Portfolio(
            userid=userid, stockname=stockname, companyname=companyname,
            totalquantity=qty, totalinvested=total_cost,
            averagebuyprice=Decimal(price), sector=stock_sector
        )
        db.session.add(new_entry)
        db.session.flush()
        portfolioid = new_entry.portfolioid

    user.money = Decimal(user.money) - total_cost
    db.session.add(user)
    
    # Assuming fifo_buy is defined and works as intended
    # fifo_buy(userid, portfolioid, companyname, qty, Decimal(price), datetime.now())
    db.session.add(Transactionhistory(
        portfolioid=portfolioid, userid=userid, stockname=stockname,
        companyname=companyname, quantity=qty, price=price,
        transactiontype="buy", timestamp=datetime.now()
    ))
    db.session.commit()
    return {"status": "ok", "action": "buy", "qty": qty, "stock": stockname}

def sell(userid, stockname, companyname, qty, price):
    fromdb = get_stock_entry(userid, stockname)
    if not fromdb or qty > fromdb.totalquantity:
        raise ValueError("Not enough shares to sell")
    
    # Assuming fifo_sell is defined and returns the cost of sold shares
    # fifo_cost = fifo_sell(userid, fromdb.portfolioid, companyname, qty, Decimal(price))
    # Simplified cost calculation for now
    fifo_cost = Decimal(fromdb.averagebuyprice) * Decimal(qty)

    fromdb.totalquantity -= qty
    fromdb.totalinvested = Decimal(fromdb.totalinvested or 0) - fifo_cost
    
    if fromdb.totalquantity > 0:
        fromdb.averagebuyprice = fromdb.totalinvested / fromdb.totalquantity
    else:
        fromdb.averagebuyprice = Decimal(0)
        fromdb.totalinvested = Decimal(0)

    user = userfromdb(userid)
    user.money = Decimal(user.money) + (Decimal(qty) * Decimal(price))
    db.session.add(user)
    
    db.session.add(Transactionhistory(
        portfolioid=fromdb.portfolioid, userid=userid, stockname=stockname,
        companyname=companyname, quantity=qty, price=price,
        transactiontype="sell", timestamp=datetime.now()
    ))
    db.session.commit()
    return {"status": "ok", "action": "sell", "qty": qty, "stock": stockname}

# ---------------- Dashboard Metrics Calculation ------------------
def calculate_user_metrics(userid):
    user = Users.query.get(userid)
    if not user: return {}

    total_investment = sum(p.totalinvested for p in Portfolio.query.filter_by(userid=userid).all() if p.totalinvested)
    holdings = gettingfromdb(userid)
    current_value = sum(h['nowvalue'] for h in holdings)
    total_pnl = current_value - float(total_investment)
    
    profit_percent = (total_pnl / float(total_investment) * 100) if total_investment > 0 else 0
    profit_score = min(max(profit_percent, 0), 100) * 0.5

    total_trades = Transactionhistory.query.filter_by(userid=userid).count()
    trade_score = min(total_trades / 20, 1) * 30

    # ✅ THIS IS THE CORRECTED LINE
    num_stocks = Portfolio.query.filter(Portfolio.userid == userid, Portfolio.totalquantity > 0).count()
    
    diversification_score = min(num_stocks / 10, 1) * 20

    total_score = profit_score + trade_score + diversification_score
    user.level = "Beginner" if total_score < 40 else "Intermediate" if total_score < 70 else "Advanced"

    today = datetime.today().date()
    streak = 0
    logins = Useractivity.query.filter_by(userid=userid, activity_type='login').order_by(Useractivity.activity_date.desc()).all()
    if logins:
        unique_login_dates = sorted(list(set(l.activity_date.date() for l in logins)), reverse=True)
        if unique_login_dates and unique_login_dates[0] == today:
            streak = 1
            for i in range(len(unique_login_dates) - 1):
                if unique_login_dates[i] - timedelta(days=1) == unique_login_dates[i+1]:
                    streak += 1
                else: break
    
    db.session.commit()
    return {"progress_score": round(total_score, 2), "level": user.level, "login_streak": streak}

# ---------------- Main Dashboard Data Aggregator ------------------
def get_dashboard_data(userid):
    user = userfromdb(userid)
    if not user: return {"error": "User not found"}

    wallet = float(user.money) if user.money else 0.0
    portfolio = gettingfromdb(userid)
    metrics = calculate_user_metrics(userid)

    investment_split = [
        {"company": h["companyname"], "stockname": h["stockname"], "sector": h["sector"], "amount": h["nowvalue"]}
        for h in portfolio if h["nowvalue"] > 0
    ]

    history = Stockhistory.query.filter_by(userid=userid).order_by(Stockhistory.dates.asc()).all()
    portfolio_value_trend, profit_loss_trend = [], []
    if history:
        df = pd.DataFrame([{"date": h.dates, "stock": h.stock_name, "close": h.close_price} for h in history])
        if not df.empty:
            daily_sum = df.groupby("date")["close"].sum().reset_index()
            daily_sum["month"] = pd.to_datetime(daily_sum["date"]).dt.strftime("%b")
            monthly_avg = daily_sum.groupby("month", sort=False)["close"].mean().reset_index()
            portfolio_value_trend = [{"date": row["month"], "value": float(row["close"])} for _, row in monthly_avg.iterrows()]
            base_val = monthly_avg["close"].iloc[0] if not monthly_avg.empty else 0
            profit_loss_trend = [{"date": row["month"], "profit_loss": float(row["close"] - base_val)} for _, row in monthly_avg.iterrows()]

    transactions = [{
        "type": t.transactiontype, "stockname": t.stockname, "price": float(t.price),
        "date": t.timestamp.strftime('%Y-%m-%d %H:%M') if t.timestamp else None
    } for t in Transactionhistory.query.filter_by(userid=userid).order_by(Transactionhistory.timestamp.desc()).limit(5)]

    return {
        "wallet": wallet, "portfolio": portfolio, "metrics": metrics,
        "investment_split": investment_split, "portfolio_value_trend": portfolio_value_trend,
        "profit_loss_trend": profit_loss_trend, "transactions": transactions
    }

