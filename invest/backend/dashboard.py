import yfinance as yf
from decimal import Decimal
from .models import Users,Portfolio,StockHistory,Transactionhistory,UserActivity,UserMilestones,Milestones
from . import db
from datetime import datetime,timedelta
import pandas as pd

def get_current_price(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get("regularMarketPrice") #current price of stock
    except Exception:
        return None

def calculate_profit_loss(stocks):
    total_invested = 0
    total_profit = 0
    total_loss = 0

    for stock in stocks:
        invested = stock['buy_price'] * stock['quantity']
        current = stock['current_price'] * stock['quantity']

        total_invested += invested
        diff = current - invested

        if diff > 0:
            total_profit += diff
        elif diff < 0:
            total_loss += abs(diff)

    # convert to percentage of total invested
    profit_percent = (total_profit / total_invested) * 100 if total_invested > 0 else 0
    loss_percent = (total_loss / total_invested) * 100 if total_invested > 0 else 0

    return profit_percent, loss_percent


# Fetch weekly historical prices for all stocks in a user's portfolio
# and store ONLY last 6 months in StockHistory table.
# Older rows beyond 6 months are automatically removed.
def update_user_portfolio_history(userid):

    portfolios = Portfolio.query.filter_by(userid=userid).all()
    result = []

    if not portfolios:
        return [{"message": "No portfolio found for this user"}]

    six_months_ago = datetime.now().date() - timedelta(days=180)

    for p in portfolios:
        symbol = str(p.stockname).strip()
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo", interval="1wk", auto_adjust=False)

            if hist is None or hist.empty:
                result.append({symbol: "No data returned"})
                continue

            # Ensure datetime index
            if not isinstance(hist.index, pd.DatetimeIndex):
                hist = hist.reset_index()
                if "Date" in hist.columns:
                    hist.set_index("Date", inplace=True)
                hist.index = pd.to_datetime(hist.index)

            # Handle Close column robustly
            if "Close" in hist.columns:
                close_series = hist["Close"]
            else:
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = ["__".join(map(str, c)) for c in hist.columns]
                close_col = next((c for c in hist.columns if "Close" in str(c)), None)
                if not close_col:
                    result.append({symbol: "No 'Close' column in data"})
                    continue
                close_series = hist[close_col]

            new_rows = 0
            for ts, close in close_series.items():
                date_val = pd.to_datetime(ts).date()
                if pd.isna(close):
                    continue
                close_val = float(close)

                existing = StockHistory.query.filter_by(
                    userid=int(userid),
                    stock_name=symbol,
                    dates=date_val
                ).first()

                if existing:
                    existing.close_price = round(close_val, 2)
                else:
                    db.session.add(StockHistory(
                        userid=int(userid),
                        stock_name=symbol,
                        dates=date_val,
                        close_price=round(close_val, 2)
                    ))
                    new_rows += 1

            # Delete rows older than 6 months (cleanup)
            StockHistory.query.filter(
                StockHistory.userid == int(userid),
                StockHistory.stock_name == symbol,
                StockHistory.dates < six_months_ago
            ).delete()

            db.session.commit()
            result.append({symbol: f"Upserted/cleaned. New rows: {new_rows}"})

        except Exception as e:
            db.session.rollback()
            result.append({symbol: f"Failed: {str(e)}"})

    return result


def calculate_user_metrics(userid):
    user = Users.query.get(userid)
    if not user:
        return {"error": "User not found"}

# 1. Progress & Level
    # Profit score (50%)
    if user.money and user.profitorloss is not None:
        profit_percent = float(user.profitorloss) / float(user.money) * 100
        profit_score = min(max(profit_percent, 0), 100) * 0.5
    else:
        profit_score = 0

    # Number of trades score (30%)
    total_trades = Transactionhistory.query.filter_by(userid=userid).count()
    trade_score = min(total_trades / 20, 1) * 30  # cap at 20 trades

    # Diversification score (20%)
    num_stocks = Portfolio.query.filter_by(userid=userid).count()
    diversification_score = min(num_stocks / 10, 1) * 20  # cap at 10 stocks

    # Total progress score
    total_score = profit_score + trade_score + diversification_score
    total_score = min(total_score, 100)

    # Determine level
    if total_score < 40:
        level = "Beginner"
    elif total_score < 70:
        level = "Intermediate"
    else:
        level = "Advanced"

    # Update user's level
    user.level = level
    db.session.commit()

    # 2. Consistency (login streak)
    today = datetime.today().date()
    streak = 0
    logins = UserActivity.query.filter_by(userid=userid, activity_type='login')\
        .order_by(UserActivity.activity_date.desc()).all()
    for login in logins:
        login_date = login.activity_date.date()
        if login_date == today - timedelta(days=streak):
            streak += 1
        else:
            break

    # 3. Milestones
    milestones_achieved = []

    # Example milestone checks:
    milestone_defs = Milestones.query.all()
    for milestone in milestone_defs:
        achieved = False
        if milestone.type == "portfolio" and num_stocks >= milestone.threshold_value:
            achieved = True
        elif milestone.type == "profit" and profit_percent >= milestone.threshold_value:
            achieved = True
        elif milestone.type == "consistency" and streak >= milestone.threshold_value:
            achieved = True


        # Check if user already has it
        if achieved and not UserMilestones.query.filter_by(userid=userid, milestone_id=milestone.milestone_id).first():
            # Add new milestone
            new_milestone = UserMilestones(
                userid=userid,
                milestone_id=milestone.milestone_id,
                achieved_on=datetime.now()
            )
            db.session.add(new_milestone)
            milestones_achieved.append(milestone.name)

    db.session.commit()

    # 4. Return combined metrics
    return {
        "progress_score": round(total_score, 2),
        "level": level,
        "login_streak": streak,
        "new_milestones": milestones_achieved
    }