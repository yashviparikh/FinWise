# import yfinance as yf
# from decimal import Decimal
# from .models import Users, Portfolio, Stockhistory, Transactionhistory, Useractivity, UserMilestones, Milestones
# from . import db
# from datetime import datetime, timedelta
# import pandas as pd
# def get_current_price(symbol: str):
#     try:
#         ticker = yf.Ticker(symbol)
#         info = ticker.info
#         return info.get("regularMarketPrice") #current price of stock
#     except Exception:
#         return None

# def calculate_profit_loss(stocks):
#     total_invested = 0
#     total_profit = 0
#     total_loss = 0

#     for stock in stocks:
#         invested = stock['buy_price'] * stock['quantity']
#         current = stock['current_price'] * stock['quantity']

#         total_invested += invested
#         diff = current - invested

#         if diff > 0:
#             total_profit += diff
#         elif diff < 0:
#             total_loss += abs(diff)

#     # convert to percentage of total invested
#     profit_percent = (total_profit / total_invested) * 100 if total_invested > 0 else 0
#     loss_percent = (total_loss / total_invested) * 100 if total_invested > 0 else 0

#     return profit_percent, loss_percent


# # Fetch weekly historical prices for all stocks in a user's portfolio
# # and store ONLY last 6 months in StockHistory table.
# # Older rows beyond 6 months are automatically removed.
# def update_user_portfolio_history(userid):

#     portfolios = Portfolio.query.filter_by(userid=userid).all()
#     result = []

#     if not portfolios:
#         return [{"message": "No portfolio found for this user"}]

#     six_months_ago = datetime.now().date() - timedelta(days=180)

#     for p in portfolios:
#         symbol = str(p.stockname).strip()
#         try:
#             ticker = yf.Ticker(symbol)
#             hist = ticker.history(period="6mo", interval="1wk", auto_adjust=False)

#             if hist is None or hist.empty:
#                 result.append({symbol: "No data returned"})
#                 continue

#             # Ensure datetime index
#             if not isinstance(hist.index, pd.DatetimeIndex):
#                 hist = hist.reset_index()
#                 if "Date" in hist.columns:
#                     hist.set_index("Date", inplace=True)
#                 hist.index = pd.to_datetime(hist.index)

#             # Handle Close column robustly
#             if "Close" in hist.columns:
#                 close_series = hist["Close"]
#             else:
#                 if isinstance(hist.columns, pd.MultiIndex):
#                     hist.columns = ["__".join(map(str, c)) for c in hist.columns]
#                 close_col = next((c for c in hist.columns if "Close" in str(c)), None)
#                 if not close_col:
#                     result.append({symbol: "No 'Close' column in data"})
#                     continue
#                 close_series = hist[close_col]

#             new_rows = 0
#             for ts, close in close_series.items():
#                 date_val = pd.to_datetime(ts).date()
#                 if pd.isna(close):
#                     continue
#                 close_val = float(close)

#                 existing = StockHistory.query.filter_by(
#                     userid=int(userid),
#                     stock_name=symbol,
#                     dates=date_val
#                 ).first()

#                 if existing:
#                     existing.close_price = round(close_val, 2)
#                 else:
#                     db.session.add(StockHistory(
#                         userid=int(userid),
#                         stock_name=symbol,
#                         dates=date_val,
#                         close_price=round(close_val, 2)
#                     ))
#                     new_rows += 1

#             # Delete rows older than 6 months (cleanup)
#             StockHistory.query.filter(
#                 StockHistory.userid == int(userid),
#                 StockHistory.stock_name == symbol,
#                 StockHistory.dates < six_months_ago
#             ).delete()

#             db.session.commit()
#             result.append({symbol: f"Upserted/cleaned. New rows: {new_rows}"})

#         except Exception as e:
#             db.session.rollback()
#             result.append({symbol: f"Failed: {str(e)}"})

#     return result


# def calculate_user_metrics(userid):
#     user = Users.query.get(userid)
#     if not user:
#         return {"error": "User not found"}

# # 1. Progress & Level
#     # Profit score (50%)
#     if user.money and user.profitorloss is not None:
#         profit_percent = float(user.profitorloss) / float(user.money) * 100
#         profit_score = min(max(profit_percent, 0), 100) * 0.5
#     else:
#         profit_score = 0

#     # Number of trades score (30%)
#     total_trades = Transactionhistory.query.filter_by(userid=userid).count()
#     trade_score = min(total_trades / 20, 1) * 30  # cap at 20 trades

#     # Diversification score (20%)
#     num_stocks = Portfolio.query.filter_by(userid=userid).count()
#     diversification_score = min(num_stocks / 10, 1) * 20  # cap at 10 stocks

#     # Total progress score
#     total_score = profit_score + trade_score + diversification_score
#     total_score = min(total_score, 100)

#     # Determine level
#     if total_score < 40:
#         level = "Beginner"
#     elif total_score < 70:
#         level = "Intermediate"
#     else:
#         level = "Advanced"

#     # Update user's level
#     user.level = level
#     db.session.commit()

#     # 2. Consistency (login streak)
#     today = datetime.today().date()
#     streak = 0
#     logins = UserActivity.query.filter_by(userid=userid, activity_type='login')\
#         .order_by(UserActivity.activity_date.desc()).all()
#     for login in logins:
#         login_date = login.activity_date.date()
#         if login_date == today - timedelta(days=streak):
#             streak += 1
#         else:
#             break

#     # 3. Milestones
#     milestones_achieved = []

#     # Example milestone checks:
#     milestone_defs = Milestones.query.all()
#     for milestone in milestone_defs:
#         achieved = False
#         if milestone.type == "portfolio" and num_stocks >= milestone.threshold_value:
#             achieved = True
#         elif milestone.type == "profit" and profit_percent >= milestone.threshold_value:
#             achieved = True
#         elif milestone.type == "consistency" and streak >= milestone.threshold_value:
#             achieved = True


#         # Check if user already has it
#         if achieved and not UserMilestones.query.filter_by(userid=userid, milestone_id=milestone.milestone_id).first():
#             # Add new milestone
#             new_milestone = UserMilestones(
#                 userid=userid,
#                 milestone_id=milestone.milestone_id,
#                 achieved_on=datetime.now()
#             )
#             db.session.add(new_milestone)
#             milestones_achieved.append(milestone.name)

#     db.session.commit()

#     # 4. Return combined metrics
#     return {
#         "progress_score": round(total_score, 2),
#         "level": level,
#         "login_streak": streak,
#         "new_milestones": milestones_achieved
#     }
# import yfinance as yf
# portfolio.py
# import yfinance as yf
# import requests
# import certifi
# from decimal import Decimal
# from datetime import datetime
# from sqlalchemy.orm.exc import NoResultFound
# import pandas as pd

# from invest.models import (
#     Users, Portfolio, Transactionhistory, FIFOLot,
#     Useractivity, Stockhistory, Stockdata, db
# )

# # --- Fix SSL issues for yfinance if needed ---
# old_get = requests.get
# def safe_get(*args, **kwargs):
#     kwargs["verify"] = certifi.where()
#     return old_get(*args, **kwargs)
# requests.get = safe_get


# # ---------------- Utils ----------------

# def getfromapi(stockname):
#     """Fetch latest price safely from yfinance."""
#     try:
#         if not stockname.endswith('.NS'):
#             ticker_symbol = f"{stockname}.NS"
#         else:
#             ticker_symbol = stockname
#         ticker = yf.Ticker(ticker_symbol)
#         hist = ticker.history(period="1d")
#         if not hist.empty:
#             return float(hist["Close"].iloc[-1])
#         return None
#     except Exception:
#         return None


# def gettingfromdb(userid):
#     """Fetch holdings + enrich with live data & P&L."""
#     rows = Portfolio.query.filter_by(userid=userid).all()
#     processed = []
#     for r in rows:
#         ltp = getfromapi(r.stockname) or float(r.averagebuyprice or 0)
#         total_quantity = r.totalquantity or 0
#         total_invested = float(r.totalinvested or 0)
#         now_value = ltp * total_quantity
#         pnl = now_value - total_invested
#         pct = (pnl / total_invested * 100) if total_invested > 0 else 0
#         processed.append({
#             "portfolioid": r.portfolioid,
#             "stockname": r.stockname,
#             "companyname": r.companyname,
#             "totalquantity": total_quantity,
#             "averagebuyprice": float(r.averagebuyprice or 0),
#             "totalinvested": total_invested,
#             "ltp": ltp,
#             "profitorloss": pnl,
#             "percentage": pct,
#             "nowvalue": now_value
#         })
#     return processed


# def get_stock_entry(userid, stockname):
#     return Portfolio.query.filter_by(userid=userid, stockname=stockname).first()


# def userfromdb(userid):
#     try:
#         return Users.query.filter_by(userid=userid).one()
#     except NoResultFound:
#         return None

# # ---------------- Buy / Sell Logic ----------------

# def buy(userid, stockname, qty, price, companyname):
#     user = userfromdb(userid)
#     if not user:
#         raise ValueError("User not found")

#     total_cost = Decimal(qty) * Decimal(price)
#     if Decimal(user.money) < total_cost:
#         raise ValueError("Insufficient funds")

#     fromdb = get_stock_entry(userid, stockname)
#     if fromdb:
#         fromdb.totalquantity += qty
#         fromdb.totalinvested += total_cost
#         fromdb.averagebuyprice = fromdb.totalinvested / fromdb.totalquantity
#         portfolioid = fromdb.portfolioid
#     else:
#         new_entry = Portfolio(
#             userid=userid,
#             stockname=stockname,
#             companyname=companyname,
#             totalquantity=qty,
#             totalinvested=total_cost,
#             averagebuyprice=Decimal(price)
#         )
#         db.session.add(new_entry)
#         db.session.flush()
#         portfolioid = new_entry.portfolioid

#     user.money = Decimal(user.money) - total_cost
#     db.session.add(user)

#     fifo_buy(userid, portfolioid, companyname, qty, Decimal(price), datetime.now())
#     db.session.add(Transactionhistory(
#         portfolioid=portfolioid, userid=userid,
#         stockname=stockname, companyname=companyname,
#         quantity=qty, price=price, transactiontype="buy", timestamp=datetime.now()
#     ))
#     db.session.add(Useractivity(userid=userid, activity_type="buy", activity_value=float(total_cost)))

#     upsert_stockhistory(userid, stockname, price)
#     upsert_stockdata(stockname, price, qty)

#     db.session.commit()
#     return {"status": "ok", "action": "buy", "qty": qty, "stock": stockname}


# def sell(userid, stockname, companyname, qty, price):
#     fromdb = get_stock_entry(userid, stockname)
#     if not fromdb or qty > fromdb.totalquantity:
#         raise ValueError("Not enough shares to sell")

#     fifo_cost = fifo_sell(userid, fromdb.portfolioid, companyname, qty, Decimal(price))
    
#     fromdb.totalquantity -= qty
#     fromdb.totalinvested -= fifo_cost
    
#     if fromdb.totalquantity > 0:
#         fromdb.averagebuyprice = fromdb.totalinvested / fromdb.totalquantity
#     else:
#         fromdb.averagebuyprice = Decimal(0)
#         fromdb.totalinvested = Decimal(0)

#     user = userfromdb(userid)
#     user.money = Decimal(user.money) + (Decimal(qty) * Decimal(price))
#     db.session.add(user)
    
#     db.session.add(Transactionhistory(
#         portfolioid=fromdb.portfolioid, userid=userid,
#         stockname=stockname, companyname=companyname,
#         quantity=qty, price=price, transactiontype="sell", timestamp=datetime.now()
#     ))
#     db.session.add(Useractivity(userid=userid, activity_type="sell", activity_value=float(qty * price)))

#     upsert_stockhistory(userid, stockname, price)
#     upsert_stockdata(stockname, price, qty)
    
#     db.session.commit()
#     return {"status": "ok", "action": "sell", "qty": qty, "stock": stockname}


# # ---------------- FIFO + Other Helpers ----------------

# def fifo_buy(userid, portfolioid, companyname, qty, price, date):
#     lot = FIFOLot(userid=userid, portfolioid=portfolioid, companyname=companyname,
#                   quantityremaining=qty, pricepershare=price, buydate=date)
#     db.session.add(lot)


# def fifo_sell(userid, portfolioid, companyname, sellqty, sellprice):
#     lots = FIFOLot.query.filter_by(
#         userid=userid, 
#         portfolioid=portfolioid, 
#         companyname=companyname
#     ).order_by(FIFOLot.buydate.asc()).all()
    
#     remaining_to_sell = sellqty
#     total_cost_of_sold_shares = Decimal(0)

#     for lot in lots:
#         if remaining_to_sell == 0:
#             break
            
#         if lot.quantityremaining <= remaining_to_sell:
#             sold_from_lot = lot.quantityremaining
#             total_cost_of_sold_shares += Decimal(sold_from_lot) * Decimal(lot.pricepershare)
#             remaining_to_sell -= sold_from_lot
#             db.session.delete(lot)
#         else:
#             sold_from_lot = remaining_to_sell
#             total_cost_of_sold_shares += Decimal(sold_from_lot) * Decimal(lot.pricepershare)
#             lot.quantityremaining -= sold_from_lot
#             db.session.add(lot)
#             remaining_to_sell = 0

#     if remaining_to_sell > 0:
#         db.session.rollback()
#         raise ValueError("FIFO logic error: Insufficient quantity in FIFO lots to sell.")

#     return total_cost_of_sold_shares


# def upsert_stockhistory(userid, stockname, price):
#     today = datetime.now().date()
#     existing = Stockhistory.query.filter_by(userid=userid, stock_name=stockname, dates=today).first()
#     if existing:
#         existing.close_price = float(price)
#     else:
#         new_history = Stockhistory(userid=userid, stock_name=stockname, dates=today, close_price=float(price))
#         db.session.add(new_history)


# def upsert_stockdata(stockname, price, qty):
#     today = datetime.now().date()
#     entry = Stockdata.query.filter_by(symbol=stockname, date=today).first()
#     if entry:
#         entry.close = price
#         entry.adj_close = price
#         entry.volume = (entry.volume or 0) + qty
#     else:
#         new_data = Stockdata(
#             symbol=stockname, date=today,
#             open=price, high=price, low=price,
#             close=price, adj_close=price, volume=qty
#         )
#         db.session.add(new_data)


# # ---------------- Dashboard Data ------------------

# def get_dashboard_data(userid):
#     """Unify portfolio + analytics for dashboard."""
#     user = userfromdb(userid)
#     if not user:
#         return {"error": "User not found"}

#     wallet = float(user.money) if user.money else 0.0
#     portfolio = gettingfromdb(userid)

#     investment_split = [
#         {"company": h["companyname"], "amount": h["nowvalue"]}
#         for h in portfolio if h["nowvalue"] > 0
#     ]

#     history = Stockhistory.query.filter_by(userid=userid).order_by(Stockhistory.dates.asc()).all()
#     portfolio_value_trend, profit_loss_trend = [], []

#     if history:
#         df = pd.DataFrame([{
#             "date": h.dates,
#             "stock": h.stock_name,
#             "close": h.close_price
#         } for h in history])

#         if not df.empty:
#             daily = df.groupby("date")["close"].sum().reset_index()
#             daily["month"] = pd.to_datetime(daily["date"]).dt.strftime("%b")

#             portfolio_value_trend = [
#                 {"month": row["month"], "value": float(row["close"])}
#                 for _, row in daily.iterrows()
#             ]

#             base_val = daily["close"].iloc[0] if not daily.empty else 1
#             profit_loss_trend = [
#                 {"month": row["month"], "pnl": float(row["close"] - base_val)}
#                 for _, row in daily.iterrows()
#             ]

#     transactions = [{
#         "type": t.transactiontype,
#         "stockname": t.stockname,
#         "price": float(t.price),
#         "date": str(t.timestamp)
#     } for t in Transactionhistory.query.filter_by(userid=userid)
#         .order_by(Transactionhistory.timestamp.desc())
#         .limit(5)
#     ]

#     return {
#         "wallet": wallet,
#         "portfolio": portfolio,
#         "investment_split": investment_split,
#         "portfolio_value_trend": portfolio_value_trend,
#         "profit_loss_trend": profit_loss_trend,
#         "transactions": transactions
#     }
from flask import Blueprint, jsonify
from .portfolio import get_dashboard_data

# Create a Blueprint for dashboard-related routes
dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard/<int:userid>", methods=["GET"])
def dashboard_route(userid):
    """
    Main endpoint for fetching all dashboard data for a given user.
    """
    try:
        data = get_dashboard_data(userid)
        if "error" in data:
            return jsonify(data), 404
        return jsonify(data)
    except Exception as e:
        # Log the exception e for debugging
        return jsonify({"error": "An internal server error occurred"}), 500