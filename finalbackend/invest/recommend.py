# recommend.py
import pandas as pd
import numpy as np
import pickle
from datetime import datetime,timedelta

# ----------------------------
# Load trained model + training columns
# ----------------------------
with open("recml_xgb.pkl", "rb") as f:
    model = pickle.load(f)

with open("training_columns.pkl", "rb") as f:
    TRAIN_COLS = pickle.load(f)

# ----------------------------
# Utility: add technical indicators
# ----------------------------
def add_technical_indicators(df):
    if "timestamp" not in df.columns:
        df["timestamp"] = datetime.now()

    df = df.sort_values("timestamp")
    df["ma5"] = df.groupby("stockname")["price"].transform(lambda x: x.rolling(5, min_periods=1).mean())
    df["ma10"] = df.groupby("stockname")["price"].transform(lambda x: x.rolling(10, min_periods=1).mean())
    df["ma20"] = df.groupby("stockname")["price"].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df["volatility"] = df.groupby("stockname")["price"].transform(lambda x: x.rolling(10, min_periods=1).std())
    df["avg_return"] = df.groupby("stockname")["price"].transform(lambda x: x.pct_change().rolling(10, min_periods=1).mean())
    df.fillna(0, inplace=True)
    return df

# ----------------------------
# Main recommendation function
# ----------------------------
def recommend_top_stocks(transactions_df, stocks_df, top_n=5):
    # 1. Start with candidate universe
    data = stocks_df.copy()

    # Ensure timestamp column exists (needed for indicators)
    data["timestamp"] = datetime.now()

    # 2. User-level features (aggregated from past transactions)
    if not transactions_df.empty:
        user_agg = transactions_df.groupby("userid").agg(
            user_total_transactions=("stockname", "count"),
            user_avg_quantity=("quantity", "mean"),
            user_avg_value=("quantity", lambda x: np.mean(x * transactions_df.loc[x.index, "price"]))
        ).reset_index()

        # Assume single user context → broadcast their stats to all stocks
        for col in user_agg.columns:
            if col != "userid":
                data[col] = user_agg[col].iloc[0]
    else:
        # cold start defaults
        data["user_total_transactions"] = 0
        data["user_avg_quantity"] = 0
        data["user_avg_value"] = 0

    # 3. Stock-level features (from transactions)
    if not transactions_df.empty:
        stock_agg = transactions_df.groupby("stockname").agg(
            stock_total_transactions=("userid", "count"),
            stock_avg_quantity=("quantity", "mean")
        ).reset_index()
        data = data.merge(stock_agg, on="stockname", how="left")

    data.fillna(0, inplace=True)
        # --- [Option 3] Add user–stock personalization ---
    if not transactions_df.empty and "userid" in transactions_df.columns:
        user_id = transactions_df["userid"].iloc[0]  # assuming single user context

        user_stock = transactions_df.groupby(["userid", "stockname"]).agg(
            user_stock_times_bought=("quantity", "count"),
            user_stock_avg_qty=("quantity", "mean"),
            user_stock_last_bought=("timestamp", "max")
        ).reset_index()

        user_stock = user_stock[user_stock["userid"] == user_id].copy()
        user_stock["days_since_last_trade"] = (
            datetime.now() - user_stock["user_stock_last_bought"]
        ).dt.days.fillna(999)

        data = data.merge(
            user_stock[["stockname", "user_stock_times_bought",
                        "user_stock_avg_qty", "days_since_last_trade"]],
            on="stockname", how="left"
        )

    # Fill missing personalization fields safely
    for col in ["user_stock_times_bought", "user_stock_avg_qty", "days_since_last_trade"]:
        if col not in data.columns:
            data[col] = 0
    data.fillna({
        "user_stock_times_bought": 0,
        "user_stock_avg_qty": 0,
        "days_since_last_trade": 999
    }, inplace=True)

    # 4. Technical indicators
    data = add_technical_indicators(data)

    # 5. Encode categorical features
    categorical_cols = ["sector", "market_cap_bucket"]
    data = pd.get_dummies(data, columns=categorical_cols)

    # 6. Align with training columns
    for col in TRAIN_COLS:
        if col not in data.columns:
            data[col] = 0
    X = data[TRAIN_COLS]

    # 7. Predict buy probabilities
    probs = model.predict_proba(X)[:, 1]
    data["buy_prob"] = probs

    # 8. Return top N recommendations
    # 8. Return top N recommendations (with exploration randomness)
    cols_to_return = [c for c in ["stockname", "companyname", "buy_prob", "price"] if c in data.columns]

    # --- [Option 2] Add slight randomness & softmax sampling for diversity ---
    # Add small Gaussian noise to break ties among similar probabilities
    data["buy_prob"] += np.random.normal(0, 0.01, len(data))

    # Compute softmax weights for probabilistic sampling
    data["softmax_prob"] = np.exp(data["buy_prob"]) / np.sum(np.exp(data["buy_prob"]))

    # Sample top N by weighted probability (adds controlled randomness)
    top_recs = data.sample(n=min(top_n, len(data)), weights=data["softmax_prob"], replace=False)

    top_recs = top_recs.sort_values("buy_prob", ascending=False).head(top_n)
    return top_recs[cols_to_return]
