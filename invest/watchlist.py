from flask import request, jsonify
from invest import db
from invest.models import Users, Stock, Watchlist, Portfolio, FIFOLot, Transactionhistory
from datetime import datetime
from decimal import Decimal
import yfinance as yf

def add_to_watchlist():
    data = request.get_json()
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


def get_watchlist(userid):
    try:
        watchlist_entries = Watchlist.query.filter_by(user_id=userid).all()
        stock_data = []

        for entry in watchlist_entries:
            stock = entry.stock
            if stock:
                symbol = stock.stock_symbol + ".NS"
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


def remove_from_watchlist(userid, stock_id):
    try:
        if not userid or not stock_id:
            return jsonify({'error': 'userid and stock_id are required'}), 400

        entry = Watchlist.query.filter_by(user_id=userid, stock_id=stock_id).first()
        if not entry:
            return jsonify({'message': 'Entry not found in watchlist'}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({'message': 'Stock removed from watchlist successfully'})

    except Exception as e:
        return jsonify({'error': f'Failed to remove stock: {str(e)}'}), 500



def buy_from_watchlist():
    data = request.get_json()
    user_id = data.get('userid')
    symbol = data.get('symbol')
    quantity = data.get('quantity')

    if not all([user_id, symbol, quantity]):
        return jsonify({'error': 'Missing data'}), 400

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        stock = Stock.query.filter_by(stock_symbol=symbol).first()
        if not stock:
            return jsonify({'error': 'Stock not found'}), 404

        ticker = yf.Ticker(symbol + ".NS")
        live_price = ticker.info.get("regularMarketPrice")

        if live_price is None:
            return jsonify({'error': 'Could not fetch live price'}), 500

        live_price = Decimal(str(live_price))
        quantity = int(quantity)
        total_cost = live_price * quantity

        if user.money < total_cost:
            return jsonify({'error': 'Insufficient funds'}), 400

        portfolio_entry = Portfolio.query.filter_by(userid=user_id, stock_id=stock.stock_id).first()

        if portfolio_entry:
            portfolio_entry.totalquantity += quantity
            portfolio_entry.totalinvested += total_cost
            portfolio_entry.averagebuyprice = portfolio_entry.totalinvested / portfolio_entry.totalquantity
        else:
            portfolio_entry = Portfolio(
                userid=user_id,
                stock_id=stock.stock_id,
                stockname=symbol + ".NS",
                companyname=stock.stock_name,
                totalquantity=quantity,
                totalinvested=total_cost,
                averagebuyprice=live_price
            )
            db.session.add(portfolio_entry)
            db.session.flush()

        user.money -= total_cost

        fifo = FIFOLot(
            userid=user_id,
            portfolioid=portfolio_entry.portfolioid,
            companyname=stock.stock_name,
            quantityremaining=quantity,
            pricepershare=live_price,
            buydate=datetime.utcnow()
        )
        db.session.add(fifo)

        txn = Transactionhistory(
            userid=user_id,
            portfolioid=portfolio_entry.portfolioid,
            companyname=stock.stock_name,
            stockname=symbol + ".NS",
            quantity=quantity,
            price=live_price,
            transactiontype="BUY",
            timestamp=datetime.utcnow()
        )
        db.session.add(txn)

        watch = Watchlist.query.filter_by(user_id=user_id, stock_id=stock.stock_id).first()
        if watch:
            db.session.delete(watch)

        db.session.commit()

        return jsonify({
            'message': f'{quantity} shares of {symbol} bought!',
            'symbol': symbol,
            'quantity': quantity,
            'price_per_share': str(live_price),
            'total_invested': str(total_cost)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to buy stock: {str(e)}'}), 500
