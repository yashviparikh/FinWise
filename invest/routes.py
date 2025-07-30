from flask import request, jsonify, render_template
from invest import app
from invest.models import Users,Stock,Watchlist,Portfolio,Transactionhistory,FIFOLot
import yfinance as yf
import pandas as pd
from invest import watchlist
from invest.portfolio import gettingfromdb, buy, sell, usercheck

stock_df = pd.read_csv('invest/stock_list.csv', dtype=str)

# ------------------- Dashboard -------------------
# @app.route('/')
# def dashboard():
#     print("hello")
#     return render_template("index.html")


# ------------------- Autocomplete & Live Price -------------------
@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '').upper()
    matches = stock_df[stock_df['Symbol'].str.contains(query, na=False)]
    suggestions = matches[['Symbol', 'Company Name']].to_dict(orient='records')
    return jsonify(suggestions)

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({'error': 'Symbol not provided'}), 400

    try:
        ticker = yf.Ticker(symbol + ".NS")
        info = ticker.info
        ltp = info.get('regularMarketPrice', 'N/A')
        change_percent = info.get('regularMarketChangePercent', 'N/A')
        return jsonify({'ltp': ltp, 'change_percent': change_percent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
# ------------------- Watchlist Routes -------------------
@app.route('/add_to_watchlist', methods=['POST'])
def add_to_watchlist_route():
    return watchlist.add_to_watchlist()

@app.route('/get_watchlist', methods=['GET'])
def get_watchlist_route():
    return watchlist.get_watchlist()

@app.route('/remove_from_watchlist', methods=['POST'])
def remove_from_watchlist_route():
    return watchlist.remove_from_watchlist()

@app.route('/buy_from_watchlist', methods=['POST'])
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




