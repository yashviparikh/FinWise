import numpy as np
import pandas as pd
import joblib
from flask import Blueprint, request, jsonify, Response, current_app, g
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_absolute_percentage_error
import csv, io, os, json, time, datetime
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import concurrent.futures

# Corrected relative imports
from .models import Users, Stock, Transactionhistory
from . import watchlist, learnings, portfolio as portfolio_module
from .portfolio import get_dashboard_data, _get_live_price_for_symbol, fetch_ltp_parallel
from . import whenmerging as base_recommend
from .whenmerging import fetch_transactions, fetch_stock_universe, recommend_top_stocks

# Blueprint
routes_bp = Blueprint("routes_bp", __name__)

# ---------------- Request timing ----------------
@routes_bp.before_request
def start_timer():
    g.start_time = time.perf_counter()

@routes_bp.after_request
def log_request_time(response):
    if hasattr(g, "start_time"):
        elapsed = time.perf_counter() - g.start_time
        print(f"[TIMER] {request.method} {request.path} took {elapsed:.3f}s")
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
    return response

# ---------------- Load stock list ----------------
try:
    CSV_PATH = os.path.join(os.path.dirname(__file__), "stock_list.csv")
    stock_df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
except (FileNotFoundError, pd.errors.EmptyDataError):
    stock_df = pd.DataFrame(columns=["SYMBOL", "NAME OF COMPANY"])

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

# ---------------- Watchlist Routes ----------------
@routes_bp.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist_route(): return watchlist.add_to_watchlist()

@routes_bp.route("/get_watchlist/<int:userid>", methods=["GET"])
def get_watchlist_route(userid): return watchlist.get_watchlist(userid)

@routes_bp.route("/remove_from_watchlist/<int:userid>/<int:stock_id>", methods=["POST"])
def remove_from_watchlist_route(userid, stock_id): return watchlist.remove_from_watchlist(userid, stock_id)

@routes_bp.route("/get_stock_id/<symbol>", methods=["GET"])
def get_stock_id(symbol):
    try:
        sym = symbol.strip().upper()
        stock = Stock.query.filter_by(stock_symbol=sym).first()
        if not stock:
            stock = Stock.query.filter_by(stock_symbol=f"{sym}.NS").first()
        if not stock:
            return jsonify({"error": f"Stock {sym} not found"}), 404
        return jsonify({"stock_id": stock.stock_id, "symbol": stock.stock_symbol, "name": stock.stock_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes_bp.route('/buy_from_watchlist', methods=['POST'])
def buy_from_watchlist_route(): return watchlist.buy_from_watchlist()

# ---------------- Portfolio & Transactions ----------------
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

# ---------------- Learnings ----------------
@routes_bp.route("/learnings/news", methods=["GET"])
def get_learnings_news():
    try:
        return jsonify(learnings.get_news())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Dashboard CSV Export ----------------
@routes_bp.route("/dashboard/<int:userid>/export", methods=["GET"])
def export_dashboard_csv(userid):
    data = get_dashboard_data(userid)
    if "error" in data: return jsonify(data), 404

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Wallet", data["wallet"]])
    cw.writerow([])
    cw.writerow(["Progress Score", data["metrics"].get("progress_score", "")])
    cw.writerow(["Level", data["metrics"].get("level", "")])
    cw.writerow(["Login Streak", data["metrics"].get("login_streak", "")])
    cw.writerow([])

    cw.writerow(["Company", "Stock", "Quantity", "Avg Buy Price", "Invested", "LTP", "Now Value", "P/L"])
    for p in data["portfolio"]:
        cw.writerow([
            p["companyname"], p["stockname"], p["totalquantity"],
            p["averagebuyprice"], p["totalinvested"],
            p["ltp"], p["nowvalue"], p["profitorloss"]
        ])
    cw.writerow([])
    cw.writerow(["Type", "Stock", "Price", "Date"])
    for t in data["transactions"]:
        cw.writerow([t["type"], t["stockname"], t["price"], t["date"]])

    output = si.getvalue()
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=dashboard_full_export.csv"})


# ---------------- Stock Prediction (UPDATED WITH DETAILED LOGS) ----------------
# ✅ REMOVED THE EXTRA, INCORRECT ROUTE DECORATOR AND THE MISPLACED IMPORT
@routes_bp.route("/predict-stock/<symbol>", methods=["GET"])
def predict_stock(symbol):
    # --- Standardize the symbol ---
    symbol = symbol.upper()
    if not symbol.endswith('.NS'):
        ticker_symbol = f"{symbol}.NS"
    else:
        ticker_symbol = symbol

    base_path = os.path.dirname(os.path.abspath(__file__))
    model_file = os.path.join(base_path, f"model_{ticker_symbol}.h5")
    scaler_file = os.path.join(base_path, f"scaler_{ticker_symbol}.joblib")
    data_file = os.path.join(base_path, f"data_{ticker_symbol}.csv")
    log_file = os.path.join(base_path, f"log_{ticker_symbol}.txt")

    df = None
    logs = ""

    # --- Attempt to load from cache ---
    try:
        model = load_model(model_file)
        scaler = joblib.load(scaler_file)
        df = pd.read_csv(data_file)
        with open(log_file, 'r') as f:
            logs = f.read()

    except FileNotFoundError:
        try:
            df = yf.download(ticker_symbol, period="8y")
            if df.empty:
                return jsonify({"error": f"No data could be downloaded for symbol '{symbol}'."}), 404

            df.reset_index(inplace=True)
            df.to_csv(data_file, index=False)

            data = df[['Close']].values
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)

            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dropout, Dense

            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(60, 1)), Dropout(0.2),
                LSTM(50, return_sequences=False), Dropout(0.2),
                Dense(25, activation="relu"), Dense(1)
            ])
            model.compile(optimizer="adam", loss="mean_squared_error")

            seq_len = 60
            x, y = [], []
            for i in range(seq_len, len(scaled_data)):
                x.append(scaled_data[i - seq_len:i, 0])
                y.append(scaled_data[i, 0])
            x, y = np.array(x), np.array(y)
            x = np.reshape(x, (x.shape[0], x.shape[1], 1))

            split = int(0.8 * len(x))
            x_train, x_test = x[:split], x[split:]
            y_train, y_test = y[:split], y[split:]

            history = model.fit(x_train, y_train, epochs=10, batch_size=32, verbose=0)
            
            log_lines = []
            for epoch, loss in enumerate(history.history['loss']):
                log_lines.append(f"Epoch {epoch+1}/10 - loss: {loss:.4f}")

            y_pred = model.predict(x_test)
            mape = mean_absolute_percentage_error(y_test, y_pred)
            accuracy = 100 * (1 - mape)
            log_lines.append(f"\nModel Accuracy: {accuracy:.1f}%")

            last_pred = scaler.inverse_transform(y_pred)[-1][0]
            second_last_pred = scaler.inverse_transform(y_pred)[-2][0]
            if last_pred > second_last_pred:
                verdict = "The model predicts an upward trend."
            else:
                verdict = "The model predicts a downward trend."
            log_lines.append(f"Final Verdict: {verdict}")

            logs = "\n".join(log_lines)
            
            with open(log_file, 'w') as f:
                f.write(logs)

            model.save(model_file)
            joblib.dump(scaler, scaler_file)

        except Exception as inner_e:
            return jsonify({"error": f"Failed to download or train model: {str(inner_e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    if df is None or df.empty:
        return jsonify({"error": "Dataframe is empty after loading/training."}), 500
    
    if "Date" not in df.columns:
        return jsonify({"error": "Critical error: 'Date' column not found in data."}), 500

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Close"]).sort_values("Date")

    data = df[['Close']].values
    scaled_data = scaler.transform(data)
    
    x_pred_data = []
    seq_len = 60
    for i in range(seq_len, len(scaled_data)):
        x_pred_data.append(scaled_data[i-seq_len:i, 0])
    x_pred_data = np.array(x_pred_data)
    x_pred_data = x_pred_data.reshape((x_pred_data.shape[0], x_pred_data.shape[1], 1))

    predictions = model.predict(x_pred_data)
    predictions_rescaled = scaler.inverse_transform(predictions)
    
    actual_data = df['Close'].values[seq_len:]

    df['MA100'] = df['Close'].rolling(100).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    
    n = 180  

    return jsonify({
        "dates": df['Date'].dt.strftime("%Y-%m-%d").iloc[-n:].tolist(),
        "actual": actual_data[-n:].flatten().tolist(),
        "predictions": predictions_rescaled[-n:].flatten().tolist(),
        "ma100": df['MA100'].values[-n:].tolist(),
        "ma200": df['MA200'].values[-n:].tolist(),
        "logs": logs
    })

# ... (rest of your routes, like recommendations, ltp, etc., are unchanged) ...
@routes_bp.route("/recommendations/<int:userid>", methods=["GET"])
def get_recommendations(userid):
    t0 = time.perf_counter()
    try:
        transactions_df = fetch_transactions(userid)
        if transactions_df.empty:
            return jsonify({"error": "No transactions found for user"}), 404

        stocks_df = fetch_stock_universe(limit=100)
        ltp_df = fetch_ltp_parallel(stocks_df["stockname"].tolist())
        stocks_df = stocks_df.merge(ltp_df, on="stockname", how="left")

        top5 = recommend_top_stocks(transactions_df, stocks_df, top_n=5)
        print(f"[PERF] TOTAL /recommendations: {time.perf_counter() - t0:.3f}s")

        return jsonify(top5.to_dict(orient="records"))
    except Exception as e:
        import traceback
        print("Error in recommendations:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@routes_bp.route("/ltp", methods=["POST"])
def ltp_batch():
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        df = fetch_ltp_parallel(symbols)
        results = {row["stockname"].upper(): row["price"] for _, row in df.iterrows() if row["price"] is not None}
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes_bp.route("/ltp/clear_cache", methods=["POST"])
def clear_ltp_cache():
    LTP_CACHE.clear()
    return jsonify({"message": "LTP cache cleared"})

# ---------------- Transactions ----------------
@routes_bp.route("/transactions/<int:userid>", methods=["GET"])
def get_transactions(userid):
    try:
        txns = Transactionhistory.query.filter_by(userid=userid).all()
        if not txns: return jsonify([])

        result = [
            {
                "userid": t.userid,
                "stockname": t.stockname,
                "quantity": t.quantity,
                "price": t.price,
                "type": t.transactiontype,
                "date": t.timestamp.strftime("%Y-%m-%d %H:%M:%S") if t.timestamp else None
            }
            for t in txns
        ]
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Failed to fetch transactions for user {userid}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500