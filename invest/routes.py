from invest import app, db
from flask import render_template, request, jsonify
from invest.models import Stock, Watchlist,Portfolio
from invest.utils import get_stock_data
import pandas as pd
import yfinance as yf

#load stock list from CSV for autocomplete
stock_df = pd.read_csv('invest/stock_list.csv', dtype=str)
stock_df.rename(columns={'SYMBOL': 'symbol', 'NAME OF COMPANY': 'name'}, inplace=True)

# @app.route('/')
# @app.route('/home')
# def all_stocks():
#     stocks = Stock.query.all()
#     return render_template("home.html", stocks=stocks)

# @app.route('/search')
# def search():
#     return render_template('search.html')

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('q', '').upper()

    if not query:
        return jsonify([])

    matches = stock_df[
        stock_df['symbol'].str.startswith(query, na=False) |
        stock_df['name'].str.upper().str.startswith(query)
    ]

    results = matches[['symbol', 'name']].dropna().head(10).to_dict(orient='records')
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

    
@app.route('/add_to_watchlist',methods=['POST'])
def add_to_watchlist():
    data = request.get_json()
    print(data)
    user_id = data.get('userid')
    stock_id = data.get('stock_id')

    if not user_id or not stock_id:
        return jsonify({'error': 'Missing userid or stock_id'}), 400

    existing = Watchlist.query.filter_by(user_id=user_id, stock_id=stock_id).first()
    if existing:
        return jsonify({'message': 'Stock already in watchlist'}), 200

    new_entry = Watchlist(user_id=user_id, stock_id=stock_id)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'message': 'Stock added to watchlist'}), 201


@app.route('/get_watchlist/<int:userid>', methods=['GET'])
def get_watchlist(userid):
    try:
        #get all stock_ids in watchlist for this user
        watchlist_entries = Watchlist.query.filter_by(user_id=userid).all()

        #fetch stock symbols from Stock table
        stock_data = []
        for entry in watchlist_entries:
            stock = entry.stock
            if stock:
                symbol = stock.stock_symbol + ".NS"
                #fetch live data using yfinance
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    price = info.get("regularMarketPrice")
                    change = info.get("regularMarketChange")
                    change_percent = info.get("regularMarketChangePercent")

                    stock_data.append({
                        'symbol': symbol,
                        'price': round(price, 2) if price else None,
                        'change': round(change, 2) if change else None,
                        'change_percent': round(change_percent, 2) if change_percent else None
                    })
                except Exception as fetch_error:
                    stock_data.append({
                        'symbol': symbol,
                        'error': f'Failed to fetch live data: {str(fetch_error)}'
                    })

        return jsonify({'watchlist': stock_data})

    except Exception as e:
        return jsonify({'error': f'Failed to get watchlist: {str(e)}'}), 500


@app.route('/remove_from_watchlist', methods=['DELETE'])
def remove_from_watchlist():
    try:
        data = request.get_json()
        print(data)
        user_id = data.get('userid')
        stock_id = data.get('stock_id')

        if not user_id or not stock_id:
            return jsonify({'error': 'user_id and stock_id are required'}), 400

        #find the watchlist entry
        entry = Watchlist.query.filter_by(user_id=user_id, stock_id=stock_id).first()

        if not entry:
            return jsonify({'message': 'Entry not found in watchlist'}), 404

        #remove stock
        db.session.delete(entry)
        db.session.commit()

        return jsonify({'message': 'Stock removed from watchlist successfully'})

    except Exception as e:
        return jsonify({'error': f'Failed to remove stock: {str(e)}'}), 500
    

@app.route('/buy_from_watchlist', methods=['POST'])
def buy_from_watchlist():
    data = request.json
    userid = data.get('userid')
    symbol=data.get('symbol')
    totalquantity = data.get('quantity')

    if not all([userid, symbol, totalquantity]):
        return jsonify({'error': 'Missing data'}), 400

    # Find stock by symbol (FIXED)
    stock = Stock.query.filter_by(stock_symbol=symbol).first()
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404

    try:
        # Fetch live price
        ticker = yf.Ticker(symbol+".NS")
        live_price = ticker.info.get('regularMarketPrice')
        if not live_price:
            return jsonify({'error': 'Could not fetch live price'}), 500

        totalinvested = round(live_price * int(totalquantity), 2)
        stockname = (symbol+".NS")
        companyname =symbol

        # Add to Portfolio
        new_entry = Portfolio(
            userid=userid,
            stock_id = stock.stock_id,
            stockname=stockname,
            companyname=companyname,
            totalquantity=totalquantity,
            totalinvested=live_price,
            averagebuyprice=totalinvested/totalquantity
        )
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({
            'message': f'{totalquantity} shares of {symbol} bought!',
            'symbol': symbol,
            'quantity': totalquantity,
            'totalinvested': totalinvested
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

















