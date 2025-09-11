from flask import request, jsonify, render_template
from . import app,db
from .models import Users,Stock,Watchlist,Portfolio,Transactionhistory,FIFOLot,StockHistory
import yfinance as yf
import pandas as pd
from . import watchlist
from .portfolio import gettingfromdb, buy, sell, usercheck
from .dashboard import calculate_profit_loss,get_current_price,update_user_portfolio_history,calculate_user_metrics
from datetime import datetime,timedelta
from sqlalchemy import func


# Load stock list once at start
stock_df = pd.read_csv('backend/stock_list.csv', dtype=str)

# ------------------- Dashboard -------------------

# @app.route('/')
# def dashboard():
#     print("hello")
#     return render_template("index.html")

@app.route('/dashboard/profit-loss/<int:userid>', methods=["GET"])
def profit_loss(userid):
    try:
        # fetch all stocks of the user from DB
        portfolios = Portfolio.query.filter_by(userid=userid).all()

        # prepare stocks in required format
        stocks = []
        for p in portfolios:
            current_price = get_current_price(p.stockname)
            if current_price:
                stocks.append({
                    "buy_price": float(p.averagebuyprice),
                    "quantity": p.totalquantity,
                    "current_price": float(current_price)
                })

        # call your function
        profit_percent, loss_percent = calculate_profit_loss(stocks)

        return jsonify({
            "profit_percent": profit_percent,
            "loss_percent": loss_percent
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/dashboard/update-portfolio-history/<int:userid>', methods=['POST'])
def update_portfolio_history(userid):
    result = update_user_portfolio_history(userid)
    return jsonify({"message": "Portfolio history updated", "details": result})

@app.route("/dashboard/performance/<int:userid>", methods=["GET"])
def portfolio_performance(userid):
    try:
        # Calculate date cutoff = today - 6 months
        six_months_ago = datetime.now() - timedelta(days=180)

        # Fetch only last 6 months of stock history for this user
        rows = (
            StockHistory.query
            .filter(StockHistory.userid == userid, StockHistory.dates >= six_months_ago)
            .order_by(StockHistory.dates.asc())
            .all()
        )

        if not rows:
            return jsonify({"message": "No stock history found"}), 404

        # Convert to DataFrame
        data = [{
            "stock_name": r.stock_name,
            "date": r.dates.strftime("%Y-%m-%d"),
            "close_price": r.close_price
        } for r in rows]

        df = pd.DataFrame(data)

        result = {}

        for stock in df["stock_name"].unique():
            stock_df = df[df["stock_name"] == stock].copy()
            stock_df = stock_df.sort_values("date")

            # First available price (within last 6 months) → baseline
            base_price = stock_df.iloc[0]["close_price"]

            # Calculate profit/loss relative to baseline
            stock_df["profit"] = stock_df["close_price"] - base_price

            result[stock] = stock_df[["date", "profit"]].to_dict(orient="records")

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/top-performing-stocks/<int:userid>", methods=["GET"])
def top_performing_stocks(userid):
    # Get all user's portfolio stocks
    user_stocks = Portfolio.query.filter_by(userid=userid).all()
    if not user_stocks:
        return jsonify({"message": "No stocks found for this user"}), 404

    stocknames = [stock.stockname for stock in user_stocks]

    # Fetch the latest price for all portfolio stocks in one query
    latest_prices_subq = (
        db.session.query(
            StockHistory.stock_name,
            func.max(StockHistory.dates).label("latest_date")
        )
        .filter(
            StockHistory.userid == userid,
            StockHistory.stock_name.in_(stocknames)
        )
        .group_by(StockHistory.stock_name)
        .subquery()
    )

    latest_prices = (
        db.session.query(
            StockHistory.stock_name,
            StockHistory.close_price
        )
        .join(
            latest_prices_subq,
            (StockHistory.stock_name == latest_prices_subq.c.stock_name) &
            (StockHistory.dates == latest_prices_subq.c.latest_date)
        )
        .all()
    )

    # Convert to dict for easy looking
    price_dict = {name: float(price) for name, price in latest_prices}

    #  Calculate profit dynamically
    stock_profits = []
    for stock in user_stocks:
        latest_price = price_dict.get(stock.stockname)
        if latest_price:
            profit = (latest_price - float(stock.averagebuyprice)) * stock.totalquantity
            if profit > 0:
                stock_profits.append({
                    "stockname": stock.stockname,
                    "companyname": stock.companyname,
                    "profit": round(profit, 2)
                })

    # Sort by profit descending and take top 3
    top_stocks = sorted(stock_profits, key=lambda x: x["profit"], reverse=True)[:3]

    return jsonify(top_stocks)


@app.route('/user/progress/<int:userid>', methods=['GET'])
def get_progress(userid):
    metrics = calculate_user_metrics(userid)
    return jsonify({
        "progress_score": metrics["progress_score"],
        "level": metrics["level"]
    })

@app.route('/user/consistency/<int:userid>', methods=['GET'])
def get_consistency(userid):
    metrics = calculate_user_metrics(userid)
    return jsonify({
        "login_streak": metrics["login_streak"]
    })

@app.route('/user/milestones/<int:userid>', methods=['GET'])
def get_milestones(userid):
    metrics = calculate_user_metrics(userid)
    return jsonify({
        "new_milestones": metrics["new_milestones"]
    })

# ------------------- Autocomplete & Live Price -------------------

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('q', '').upper()

    if not query:
        return jsonify([])

    matches = stock_df[
        stock_df['SYMBOL'].str.upper().str.startswith(query, na=False) |
        stock_df['NAME OF COMPANY'].str.upper().str.startswith(query, na=False)
    ]

    results = matches[['SYMBOL', 'NAME OF COMPANY']].dropna().head(10).to_dict(orient='records')
    return jsonify(results)


@app.route('/get-price/<symbol>', methods=['GET'])
def get_live_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get("regularMarketPrice")
        previous_close = info.get("previousClose")

        if price is not None and previous_close:
            change = round(price - previous_close, 2)
            change_percent = round((change / previous_close) * 100, 2)

            return jsonify({
                'symbol': symbol.upper(),
                'price': round(price, 2),
                'change': change,
                'change_percent': change_percent
            })
        else:
            return jsonify({'error': 'Price data incomplete'}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to fetch price for {symbol}: {str(e)}'}), 500

    
# ------------------- Watchlist Routes -------------------

@app.route('/add_to_watchlist', methods=['POST']) #takes userid and stockid
def add_to_watchlist_route():
    return watchlist.add_to_watchlist()

@app.route('/get_watchlist/<int:userid>', methods=['GET'])
def get_watchlist_route(userid):
    return watchlist.get_watchlist(userid)

@app.route('/remove_from_watchlist/<int:userid>/<int:stock_id>', methods=['POST'])
def remove_from_watchlist_route(userid,stock_id):
    return watchlist.remove_from_watchlist(userid,stock_id)

@app.route('/buy_from_watchlist', methods=['POST'])#takes userid, symbol and qty
def buy_from_watchlist_route():
    return watchlist.buy_from_watchlist()


# ------------------- Portfolio Routes -------------------

@app.route('/portfolio/<int:userid>', methods=['GET'])
def getportfoliofromuserid(userid):
    try:
        data = gettingfromdb(userid)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/buy', methods=['POST'])
def buystock(): 
    data = request.get_json()
    try:
        buy(
            userid=data['userid'],
            stockname=data['stockname'],
            qty=int(data['qty']),
            price=float(data['price']),
            companyname=data['companyname']
        )
        return jsonify({"message": "Buy successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sell', methods=['POST'])
def sell_stock():
    data = request.get_json()
    try:
        sell(
            userid=data['userid'],
            stockname=data['stockname'],
            qty=int(data['qty']),
            price=float(data['price']),
            companyname=data['companyname']
        )
        return jsonify({"message": "Sell successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user/<int:userid>', methods=['GET'])
def get_user(userid):
    try:
        user = usercheck(userid)
        return jsonify(user)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




