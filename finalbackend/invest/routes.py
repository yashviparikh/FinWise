        # from flask import request, jsonify, render_template
        # from invest import app
        # from invest.models import Users,Stock,Watchlist,Portfolio,Transactionhistory,FIFOLot
        # import yfinance as yf
        # import pandas as pd
        # from invest import watchlist, learnings
        # from invest.portfolio import gettingfromdb, buy, sell, usercheck
        # import os


        # # Load stock list once at start
        # stock_df = pd.read_csv('invest/stock_list.csv', dtype=str)

        # # ------------------- Dashboard -------------------

        # @app.route('/')
        # def dashboard():
        #     #print("hello")
        #     return render_template("index.html")


        # # ------------------- Autocomplete & Live Price -------------------

        # @app.route('/autocomplete')
        # def autocomplete():
        #     query = request.args.get('q', '').upper()

        #     if not query:
        #         return jsonify([])

        #     matches = stock_df[
        #         stock_df['SYMBOL'].str.upper().str.startswith(query, na=False) |
        #         stock_df['NAME OF COMPANY'].str.upper().str.startswith(query, na=False)
        #     ]

        #     results = matches[['SYMBOL', 'NAME OF COMPANY']].dropna().head(10).to_dict(orient='records')
        #     return jsonify(results)


        # @app.route('/get-price/<symbol>', methods=['GET'])
        # def get_live_price(symbol):
        #     try:
        #         ticker = yf.Ticker(symbol)
        #         info = ticker.info

        #         price = info.get("regularMarketPrice")
        #         previous_close = info.get("previousClose")

        #         if price is not None and previous_close:
        #             change = round(price - previous_close, 2)
        #             change_percent = round((change / previous_close) * 100, 2)

        #             return jsonify({
        #                 'symbol': symbol.upper(),
        #                 'price': round(price, 2),
        #                 'change': change,
        #                 'change_percent': change_percent
        #             })
        #         else:
        #             return jsonify({'error': 'Price data incomplete'}), 404
        #     except Exception as e:
        #         return jsonify({'error': f'Failed to fetch price for {symbol}: {str(e)}'}), 500

            
        # # ------------------- Watchlist Routes -------------------

        # @app.route('/add_to_watchlist', methods=['POST']) #takes userid and stockid
        # def add_to_watchlist_route():
        #     return watchlist.add_to_watchlist()

        # @app.route('/get_watchlist/<int:userid>', methods=['GET'])
        # def get_watchlist_route(userid):
        #     return watchlist.get_watchlist(userid)

        # @app.route('/remove_from_watchlist/<int:userid>/<int:stock_id>', methods=['POST'])
        # def remove_from_watchlist_route(userid,stock_id):
        #     return watchlist.remove_from_watchlist(userid,stock_id)

        # @app.route('/buy_from_watchlist', methods=['POST'])#takes userid, symbol and qty
        # def buy_from_watchlist_route():
        #     return watchlist.buy_from_watchlist()


        # # ------------------- Portfolio Routes -------------------

        # @app.route('/portfolio/<int:userid>', methods=['GET'])
        # def getportfoliofromuserid(userid):
        #     try:
        #         data = gettingfromdb(userid)
        #         return jsonify(data)
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500

        # @app.route('/buy', methods=['POST'])
        # def buystock(): 
        #     data = request.get_json()
        #     try:
        #         buy(
        #             userid=data['userid'],
        #             stockname=data['stockname'],
        #             qty=int(data['qty']),
        #             price=float(data['price']),
        #             companyname=data['companyname']
        #         )
        #         return jsonify({"message": "Buy successful"})
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500

        # @app.route('/sell', methods=['POST'])
        # def sell_stock():
        #     data = request.get_json()
        #     try:
        #         sell(
        #             userid=data['userid'],
        #             stockname=data['stockname'],
        #             qty=int(data['qty']),
        #             price=float(data['price']),
        #             companyname=data['companyname']
        #         )
        #         return jsonify({"message": "Sell successful"})
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500

        # @app.route('/user/<int:userid>', methods=['GET'])
        # def get_user(userid):
        #     try:
        #         user = usercheck(userid)
        #         return jsonify(user)
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500
            

        # # ------------------- Learnings -------------------

        # @app.route('/learnings', methods=['GET'])
        # def get_learnings():
        #     try:
        #         data = learnings.get_news()
        #         return jsonify(data)
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500


        # @app.route('/learnings/refresh', methods=['POST'])
        # def refresh_learnings():
        #     try:
        #         # Force refresh by deleting cache
        #         cache_path = "cache_news.json"
        #         if os.path.exists(cache_path):
        #             os.remove(cache_path)

        #         data = learnings.get_news()
        #         return jsonify({
        #             "message": "News refreshed successfully",
        #             "data": data
        #         })
        #     except Exception as e:
        #         return jsonify({"error": str(e)}), 500

        # invest/routes.py
        # routes.py

import numpy as np
import pandas as pd
import joblib
from flask import Blueprint, request, jsonify
from tensorflow.keras.models import load_model
from invest.models import Users, Stock
from invest import watchlist, learnings, portfolio as portfolio_module
from .portfolio import get_dashboard_data
import csv,io,os,json,time
from flask import Response, current_app
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

import invest.whenmerging as base_recommend

# This Blueprint will handle all routes EXCEPT the main dashboard
routes_bp = Blueprint("routes_bp", __name__)

# --- Load stock list CSV safely ---
try:
    CSV_PATH = os.path.join(os.path.dirname(__file__), "stock_list.csv")
    stock_df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
except (FileNotFoundError, pd.errors.EmptyDataError):
    stock_df = pd.DataFrame(columns=["SYMBOL", "NAME OF COMPANY"])


CACHE_FILE = "price_cache.json"
CACHE_TTL = 300  # 5 min

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        _price_cache = json.load(f)
else:
    _price_cache = {}

def _save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(_price_cache, f)


# --- Helper for live price ---
def _get_live_price_for_symbol(symbol_plain):
    try:
        ticker_symbol = f"{symbol_plain.upper()}.NS"
        t = yf.Ticker(ticker_symbol)
        info = t.info or {}
        price = info.get("regularMarketPrice") or info.get("previousClose")
        prev = info.get("previousClose")
        if price is None: return None, None, None
        
        change = round(float(price) - float(prev), 2) if prev else 0
        change_percent = round((change / float(prev)) * 100, 2) if prev and prev != 0 else 0
        return round(float(price), 2), change, change_percent
    except Exception:
        return None, None, None


# --- General and Info Routes ---
@routes_bp.route("/")
def index():
    return jsonify({"status": "ok", "message": "API is running"})

@routes_bp.route("/autocomplete")
def autocomplete():
    q = (request.args.get("q") or "").strip().upper()
    if not q or stock_df.empty: return jsonify([])
    
    mask = stock_df["SYMBOL"].str.upper().str.startswith(q) | stock_df["NAME OF COMPANY"].str.upper().str.startswith(q)
    matches = stock_df[mask].head(10)
    results = matches[["SYMBOL", "NAME OF COMPANY"]].to_dict(orient="records")
    return jsonify(results)

@routes_bp.route("/get-price/<symbol>", methods=["GET"])
def get_price(symbol):
    price, change, change_percent = _get_live_price_for_symbol(symbol)
    if price is None: return jsonify({"error": "Price not available"}), 404
    return jsonify({"symbol": symbol, "price": price, "change": change, "change_percent": change_percent})

@routes_bp.route("/get_wallet/<int:userid>", methods=["GET"])
def get_wallet_route(userid):
    user = Users.query.get(userid)
    if not user: return jsonify({"error": "User not found"}), 404
    return jsonify({"money": float(user.money or 0)})


# --- Watchlist Routes ---
@routes_bp.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist_route(): return watchlist.add_to_watchlist()

@routes_bp.route("/get_watchlist/<int:userid>", methods=["GET"])
def get_watchlist_route(userid): return watchlist.get_watchlist(userid)

@routes_bp.route("/remove_from_watchlist/<int:userid>/<int:stock_id>", methods=["POST"])
def remove_from_watchlist_route(userid, stock_id): return watchlist.remove_from_watchlist(userid, stock_id)


@routes_bp.route("/get_stock_id/<symbol>", methods=["GET"])
def get_stock_id(symbol):
    try:
        # Normalize symbol
        sym = symbol.strip().upper()

        # Try to match stock_symbol directly
        stock = Stock.query.filter_by(stock_symbol=sym).first()

        # If not found, try with ".NS"
        if not stock:
            stock = Stock.query.filter_by(stock_symbol=f"{sym}.NS").first()

        if not stock:
            return jsonify({"error": f"Stock {sym} not found"}), 404

        return jsonify({"stock_id": stock.stock_id, "symbol": stock.stock_symbol, "name": stock.stock_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes_bp.route('/buy_from_watchlist', methods=['POST'])#takes userid, symbol and qty
def buy_from_watchlist_route():
     return watchlist.buy_from_watchlist()

# --- Portfolio & Transaction Routes ---
@routes_bp.route("/portfolio/<int:userid>", methods=["GET"])
def get_portfolio(userid):
    try:
        holdings = portfolio_module.gettingfromdb(userid)
        return jsonify(holdings)
    except Exception as e:
        current_app.logger.error(f"Failed to get portfolio for user {userid}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@routes_bp.route("/buy", methods=["POST"])
def buystock():
    try:
        data = request.get_json() or {}
        result = portfolio_module.buy(
            userid=int(data["userid"]), stockname=data["stockname"],
            qty=int(data["qty"]), price=float(data["price"]), companyname=data["companyname"]
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes_bp.route("/sell", methods=["POST"])
def sell_stock():
    try:
        data = request.get_json() or {}
        result = portfolio_module.sell(
            userid=int(data["userid"]), stockname=data["stockname"],
            companyname=data["companyname"], qty=int(data["qty"]), price=float(data["price"])
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Learnings Routes ---
@routes_bp.route("/learnings/news", methods=["GET"])
def get_learnings_news():
    try:
        return jsonify(learnings.get_news())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes_bp.route("/dashboard/<int:userid>/export", methods=["GET"])
def export_dashboard_csv(userid):
    data = get_dashboard_data(userid)
    if "error" in data:
        return jsonify(data), 404

    si = io.StringIO()
    cw = csv.writer(si)

    # First section: Wallet + Metrics
    cw.writerow(["Wallet", data["wallet"]])
    cw.writerow([])
    cw.writerow(["Progress Score", data["metrics"].get("progress_score", "")])
    cw.writerow(["Level", data["metrics"].get("level", "")])
    cw.writerow(["Login Streak", data["metrics"].get("login_streak", "")])
    cw.writerow([])

    # Portfolio section
    cw.writerow(["Company", "Stock", "Quantity", "Avg Buy Price", "Invested", "LTP", "Now Value", "P/L"])
    for p in data["portfolio"]:
        cw.writerow([
            p["companyname"], p["stockname"], p["totalquantity"],
            p["averagebuyprice"], p["totalinvested"],
            p["ltp"], p["nowvalue"], p["profitorloss"]
        ])
    cw.writerow([])

    # Transactions section
    cw.writerow(["Type", "Stock", "Price", "Date"])
    for t in data["transactions"]:
        cw.writerow([t["type"], t["stockname"], t["price"], t["date"]])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=dashboard_full_export.csv"}
    )

@routes_bp.route("/predict-stock/<symbol>", methods=["GET"])
def predict_stock(symbol):
    symbol = symbol.upper()

    base_path = os.path.dirname(os.path.abspath(__file__))
    model_file = os.path.join(base_path, f"model_{symbol}.NS.h5")
    scaler_file = os.path.join(base_path, f"scaler_{symbol}.NS.joblib")
    data_file = os.path.join(base_path, f"data_{symbol}.NS.csv")

    try:
        # --- Try cached version
        model = load_model(model_file)
        scaler = joblib.load(scaler_file)
        df = pd.read_csv(data_file)
        logs = f"✅ Loaded cached model for {symbol}."
    except Exception:
        # --- Fallback: train new model
        try:
            import yfinance as yf
            df = yf.download(f"{symbol}.NS", period="8y")
            if df.empty:
                return jsonify({"error": f"No data available for {symbol}"}), 404

            data = df[['Close']].values
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)

            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dropout, Dense

            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(60, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25, activation="relu"),
                Dense(1)
            ])
            model.compile(optimizer="adam", loss="mean_squared_error")

            # Sequences
            seq_len = 60
            x, y = [], []
            for i in range(seq_len, len(scaled_data)):
                x.append(scaled_data[i - seq_len:i, 0])
                y.append(scaled_data[i, 0])
            x, y = np.array(x), np.array(y)
            x = np.reshape(x, (x.shape[0], x.shape[1], 1))

            split = int(0.8 * len(x))
            x_train, y_train = x[:split], y[:split]
            model.fit(x_train, y_train, epochs=20, batch_size=32, verbose=0)

            # Save for next time
            model.save(model_file)
            joblib.dump(scaler, scaler_file)
            df.reset_index().to_csv(data_file, index=False)
            logs = f"⚠️ Fallback: trained new model for {symbol}."
        except Exception as inner_e:
            return jsonify({"error": f"Model and fallback failed: {str(inner_e)}"}), 500

    # --- Ensure Date column is correct
    if "Date" not in df.columns:
        df = df.reset_index()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.sort_values("Date")

    # --- Prediction
    seq_len = 60
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    data = df[['Close']].values
    scaled_data = scaler.transform(data)

    x = np.array([scaled_data[i - seq_len:i, 0] for i in range(seq_len, len(scaled_data))])
    x = x.reshape((x.shape[0], x.shape[1], 1))

    predictions = model.predict(x)
    predictions_rescaled = scaler.inverse_transform(predictions)
    y_test_rescaled = data[seq_len:]

    df['MA100'] = df['Close'].rolling(100).mean()
    df['MA200'] = df['Close'].rolling(200).mean()

    n = 180
    return jsonify({
        "dates": df['Date'].dt.strftime("%Y-%m-%d").iloc[-n:].tolist(),
        "actual": y_test_rescaled[-n:].flatten().tolist(),
        "predictions": predictions_rescaled[-n:].flatten().tolist(),
        "ma100": df['MA100'].values[-n:].tolist(),
        "ma200": df['MA200'].values[-n:].tolist(),
        "logs": logs
    })

@routes_bp.route("/ltp", methods=["POST"])
def get_ltp():
    """
    Returns last traded prices for given stock symbols.
    Expects: { "symbols": ["INFY","TCS",...] }
    """
    data = request.get_json()
    symbols = data.get("symbols", [])
    now = time.time()
    prices = {}

    for sym in symbols:
        sym = str(sym)
        cached = _price_cache.get(sym)
        if cached:
            price, ts = cached
            if now - ts < CACHE_TTL:
                prices[sym] = price
                continue
        try:
            price, _, _ = _get_live_price_for_symbol(sym)
            if price:
                prices[sym] = price
                _price_cache[sym] = (price, now)
        except Exception:
            if cached:
                price, _ = cached
                prices[sym] = price
    _save_cache()
    return jsonify(prices)

# ----------------------------
# Recommendations endpoint
# ----------------------------
@routes_bp.route("/recommendations/<int:userid>", methods=["GET"])
def get_recommendations(userid):
    """
    Generate top 5 stock recommendations for given user.
    """
    try:
        transactions_df = base_recommend.fetch_portfolio(userid)
        stocks_df = base_recommend.fetch_stock_universe(limit=100)
        ltp_df = base_recommend.fetch_ltp(stocks_df["stockname"].tolist())
        stocks_df = stocks_df.merge(ltp_df, on="stockname", how="left")

        recs = base_recommend.recommend_top_stocks(transactions_df, stocks_df, top_n=5)
        return jsonify(recs.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500