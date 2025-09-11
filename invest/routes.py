from flask import request, jsonify, render_template
from invest import app
from invest.models import Users,Stock,Watchlist,Portfolio,Transactionhistory,FIFOLot
import yfinance as yf
import pandas as pd
from invest import watchlist, learnings
from invest.portfolio import gettingfromdb, buy, sell, usercheck
import os


# Load stock list once at start
stock_df = pd.read_csv('invest/stock_list.csv', dtype=str)

# ------------------- Dashboard -------------------

@app.route('/')
def dashboard():
    #print("hello")
    return render_template("index.html")


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
    

# ------------------- Learnings -------------------

@app.route('/learnings', methods=['GET'])
def get_learnings():
    try:
        data = learnings.get_news()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/learnings/refresh', methods=['POST'])
def refresh_learnings():
    try:
        # Force refresh by deleting cache
        cache_path = "cache_news.json"
        if os.path.exists(cache_path):
            os.remove(cache_path)

        data = learnings.get_news()
        return jsonify({
            "message": "News refreshed successfully",
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500





