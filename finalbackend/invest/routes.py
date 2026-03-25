import numpy as np
import pandas as pd
import joblib
from flask import Blueprint, request, jsonify, Response, current_app, g
from flask_cors import cross_origin
from sklearn.metrics import mean_absolute_percentage_error
import csv, io, os, json, time, datetime
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import concurrent.futures

# Corrected relative imports
from .models import Users, Stock, Transactionhistory
from . import watchlist, learnings, portfolio as portfolio_module
from .portfolio import get_dashboard_data, _get_live_price_for_symbol, fetch_ltp_parallel
from . import trade_simulator
from . import whenmerging as base_recommend
from .whenmerging import fetch_transactions, fetch_stock_universe, recommend_top_stocks
from .auth import require_user

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


@routes_bp.route("/api/simulate-trade/history", methods=["GET"])
def simulate_trade_history():
    symbol = (request.args.get("symbol") or "").strip()
    range_key = (request.args.get("range") or "6M").strip().upper()
    result = trade_simulator.fetch_history(symbol, range_key)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@routes_bp.route("/api/simulate-trade", methods=["POST"])
def simulate_trade_api():
    payload = request.get_json() or {}
    result, status = trade_simulator.simulate_trade(payload)
    return jsonify(result), status

@routes_bp.route("/get-price/<symbol>", methods=["GET"])
def get_price(symbol):
    price, change, change_percent = _get_live_price_for_symbol(symbol)
    if price is None: return jsonify({"error": "Price not available"}), 404
    return jsonify({"symbol": symbol, "price": price, "change": change, "change_percent": change_percent})

@routes_bp.route("/get_wallet/<int:userid>", methods=["GET"])
@require_user
def get_wallet_route(userid):
    user = Users.query.get(userid)
    if not user: return jsonify({"error": "User not found"}), 404
    return jsonify({"money": float(user.money or 0)})

@routes_bp.route("/portfolio/<int:userid>/backfill_sectors", methods=["POST"])
@require_user
def backfill_sectors_route(userid):
    try:
        res = portfolio_module.backfill_sectors(userid)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Watchlist Routes ----------------
@routes_bp.route("/add_to_watchlist", methods=["POST"])
@require_user
def add_to_watchlist_route(): return watchlist.add_to_watchlist()

@routes_bp.route("/get_watchlist/<int:userid>", methods=["GET"])
@require_user
def get_watchlist_route(userid): return watchlist.get_watchlist(userid)

@routes_bp.route("/remove_from_watchlist/<int:userid>/<int:stock_id>", methods=["POST"])
@require_user
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
@require_user
def buy_from_watchlist_route(): return watchlist.buy_from_watchlist()

# ---------------- Portfolio & Transactions ----------------
@routes_bp.route("/portfolio/<int:userid>", methods=["GET"])
@require_user
def get_portfolio(userid):
    try:
        holdings = portfolio_module.gettingfromdb(userid)
        return jsonify(holdings)
    except Exception as e:
        current_app.logger.error(f"Failed to get portfolio for user {userid}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@routes_bp.route("/buy", methods=["POST"])
@require_user
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
@require_user
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
# Removed the extra incorrect route decorator and the misplaced import
@routes_bp.route("/predict-stock/<symbol>", methods=["GET", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)
def predict_stock(symbol):
    # --- Standardize and sanitize the symbol ---
    # Keep the original ticker for yfinance (after upper/strip and adding .NS),
    # but use a filesystem-safe variant for filenames (Windows doesn't allow : * ? " < > |)
    import re
    symbol = (symbol or "").strip().upper()
    if not symbol:
        return jsonify({"error": "Missing stock symbol"}), 400
    if not symbol.endswith('.NS'):
        ticker_symbol = f"{symbol}.NS"
    else:
        ticker_symbol = symbol

    base_path = os.path.dirname(os.path.abspath(__file__))
    safe_ticker_for_fs = re.sub(r'[<>:"/\\|?*]', '_', ticker_symbol)  # Windows-safe
    model_file = os.path.join(base_path, f"model_{safe_ticker_for_fs}.h5")
    scaler_file = os.path.join(base_path, f"scaler_{safe_ticker_for_fs}.joblib")
    data_file = os.path.join(base_path, f"data_{safe_ticker_for_fs}.csv")
    log_file = os.path.join(base_path, f"log_{safe_ticker_for_fs}.txt")

    df = None
    logs = ""

    # preflight is handled by the @cross_origin decorator; normal GET handling continues

    # --- Attempt to load from cache ---
    try:
        from keras.models import load_model
        model = load_model(model_file)
        scaler = joblib.load(scaler_file)
        df = pd.read_csv(data_file)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
        except Exception:
            logs = ""

    except FileNotFoundError:
        try:
            # yfinance sometimes returns MultiIndex columns; we'll normalize later
            df = yf.download(ticker_symbol, period="8y")
            if df.empty:
                return jsonify({"error": f"No data could be downloaded for symbol '{symbol}'."}), 404

            df.reset_index(inplace=True)
            df.to_csv(data_file, index=False)

            # If Close missing due to schema differences, ensure_date_close will fix below before prediction
            data = df[['Close']].values if 'Close' in df.columns else df.select_dtypes(include=[np.number]).iloc[:, :1].values
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)

            from keras.models import Sequential
            from keras.layers import LSTM, Dropout, Dense

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

            if len(x) == 0:
                return jsonify({"error": "Not enough historical data to train the model for this symbol."}), 400
            split = max(1, int(0.8 * len(x)))
            x_train, x_test = x[:split], x[split:]
            y_train, y_test = y[:split], y[split:]

            history = model.fit(x_train, y_train, epochs=10, batch_size=32, verbose=0)
            
            log_lines = []
            for epoch, loss in enumerate(history.history['loss']):
                log_lines.append(f"Epoch {epoch+1}/10 - loss: {loss:.4f}")

            # Guard against empty test split
            y_pred = model.predict(x_test) if len(x_test) else model.predict(x_train)
            # Match shapes for metric
            y_true_for_metric = y_test if len(x_test) else y_train
            mape = mean_absolute_percentage_error(y_true_for_metric, y_pred)
            accuracy = 100 * (1 - mape)
            log_lines.append(f"\nModel Accuracy: {accuracy:.1f}%")

            inv_preds = scaler.inverse_transform(y_pred.reshape(-1, 1))
            last_pred = inv_preds[-1][0]
            second_last_pred = inv_preds[-2][0] if inv_preds.shape[0] > 1 else last_pred
            if last_pred > second_last_pred:
                verdict = "The model predicts an upward trend."
            else:
                verdict = "The model predicts a downward trend."
            log_lines.append(f"Final Verdict: {verdict}")

            logs = "\n".join(log_lines)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(logs)

            model.save(model_file)
            joblib.dump(scaler, scaler_file)

        except Exception as inner_e:
            return jsonify({"error": f"Failed to download or train model: {str(inner_e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    # Ensure df has Date and Close columns (handle different CSV schemas)
    def ensure_date_close(input_df):
        # If input is not a DataFrame (e.g., numpy array), try to coerce it
        if input_df is None:
            return pd.DataFrame()
        if not isinstance(input_df, pd.DataFrame):
            try:
                d = pd.DataFrame(input_df)
            except Exception:
                # give up and return empty DF
                return pd.DataFrame()
        else:
            d = input_df.copy()

        # ensure we can iterate columns safely
        try:
            cols_map = {c.lower(): c for c in d.columns}
        except Exception:
            cols_map = {}

        # Date
        if 'date' in cols_map:
            try:
                d['Date'] = pd.to_datetime(d[cols_map['date']], errors='coerce')
            except Exception:
                d['Date'] = pd.NaT
        else:
            # try index
            try:
                d['Date'] = pd.to_datetime(d.index)
            except Exception:
                d['Date'] = pd.NaT

        # Close
        close_col = None
        for candidate in ('close', 'adj close', 'adjclose'):
            if candidate in cols_map:
                close_col = cols_map[candidate]
                break
        if close_col is None and 'Close' in d.columns:
            close_col = 'Close'
        if close_col is None:
            # fallback: first numeric column
            num_cols = d.select_dtypes(include=[np.number]).columns.tolist()
            if num_cols:
                close_col = num_cols[0]

        # Safely extract a single-series for the Close column. Pandas can return a DataFrame
        # if the column selector is ambiguous (e.g., MultiIndex or list-like). Handle that.
        if close_col is not None:
            try:
                series_candidate = d[close_col]
                # If the selection returns a DataFrame (e.g., MultiIndex), pick the first column
                if isinstance(series_candidate, pd.DataFrame):
                    if series_candidate.shape[1] >= 1:
                        series_candidate = series_candidate.iloc[:, 0]
                    else:
                        # no usable column
                        series_candidate = pd.Series([np.nan] * len(d), index=d.index)
                # If it's not a Series/ndarray/list, attempt to coerce to a Series
                if not isinstance(series_candidate, (pd.Series, list, tuple, np.ndarray)):
                    series_candidate = pd.Series(series_candidate)
            except Exception:
                # final fallback: use first numeric column if available
                num_cols = d.select_dtypes(include=[np.number]).columns.tolist()
                if num_cols:
                    series_candidate = d[num_cols[0]]
                else:
                    series_candidate = pd.Series([np.nan] * len(d), index=d.index)

            d['Close'] = pd.to_numeric(series_candidate, errors='coerce')
        else:
            d['Close'] = np.nan

        return d

    raw_df = df
    df = ensure_date_close(df)
    if df is None or df.empty:
        return jsonify({"error": "Dataframe is empty after loading/training."}), 500
    # Ensure the expected columns exist (defensive: avoid KeyError when dropna is called)
    if 'Date' not in df.columns:
        df['Date'] = pd.NaT
    if 'Close' not in df.columns:
        df['Close'] = np.nan

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Defensive handling: ensure df['Close'] is a 1-D Series/array before to_numeric
    try:
        close_candidate = df['Close']
        if isinstance(close_candidate, pd.DataFrame):
            # pick first column if DataFrame
            if close_candidate.shape[1] >= 1:
                close_candidate = close_candidate.iloc[:, 0]
            else:
                close_candidate = pd.Series([np.nan] * len(df), index=df.index)
        if not isinstance(close_candidate, (pd.Series, list, tuple, np.ndarray)):
            close_candidate = pd.Series(close_candidate)
        df['Close'] = pd.to_numeric(close_candidate, errors='coerce')
    except Exception:
        # last-resort: try to coerce any numeric columns, otherwise fill NaN
        try:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if num_cols:
                df['Close'] = pd.to_numeric(df[num_cols[0]], errors='coerce')
            else:
                df['Close'] = np.nan
        except Exception:
            df['Close'] = np.nan
    df = df.dropna(subset=['Date', 'Close']).sort_values('Date')
    if df.empty:
        # save a sample of the problematic dataframe to help debugging
        try:
            sample_path = log_file.replace('.txt', '_bad_sample.csv')
            # write raw rows so we can inspect schema
            try:
                pd.DataFrame(raw_df).head(20).to_csv(sample_path, index=False)
            except Exception:
                # best-effort: write string repr
                with open(sample_path, 'w', encoding='utf-8') as sf:
                    sf.write(repr(raw_df)[:10000])
        except Exception:
            sample_path = None
        payload = {"error": "No valid Date/Close rows after sanitization."}
        if sample_path:
            payload["sample_file"] = os.path.basename(sample_path)
        return jsonify(payload), 500

    data = df[['Close']].values
    try:
        scaled_data = scaler.transform(data)
    except Exception as e:
        return jsonify({"error": f"Failed to scale data: {str(e)}"}), 500
    
    x_pred_data = []
    seq_len = 60
    for i in range(seq_len, len(scaled_data)):
        x_pred_data.append(scaled_data[i-seq_len:i, 0])
    x_pred_data = np.array(x_pred_data)
    if x_pred_data.size == 0:
        return jsonify({"error": "Not enough data to generate predictions (need at least 60 data points)."}), 400
    x_pred_data = x_pred_data.reshape((x_pred_data.shape[0], x_pred_data.shape[1], 1))

    predictions = model.predict(x_pred_data)
    predictions_rescaled = scaler.inverse_transform(predictions.reshape(-1, 1))
    
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
    try:
        portfolio_module.LTP_CACHE.clear()
    except Exception:
        pass
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
