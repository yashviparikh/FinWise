# recommend.py
import pandas as pd
import numpy as np
import pickle
from datetime import datetime

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
    cols_to_return = [c for c in ["stockname", "companyname", "buy_prob", "price"] if c in data.columns]
    top_recs = data.sort_values("buy_prob", ascending=False).head(top_n)

    return top_recs[cols_to_return]


# ----------------------------
# Example usage (demo)
# ----------------------------
import pandas as pd

# Hardcoded transactions only for user1
transactions_data = [
    [1, "RELIANCE", "2024-06-05", "BUY", 10, 2850.50],
    [ 1, "TCS", "2024-06-06", "BUY", 5, 3780.75],
    [1, "HDFC", "2024-06-08", "BUY", 12, 1620.00],
    [1, "ICICI", "2024-06-09", "BUY", 15, 995.40],
    [1, "BHARTIARTL", "2024-06-11", "BUY", 10, 1295.80],
    [1, "BAJFINANCE", "2024-06-14", "BUY", 3, 7150.00],
    [1, "HINDUNILVR", "2024-06-15", "BUY", 7, 2480.35],
    [1, "KOTAKBANK", "2024-06-17", "BUY", 8, 1825.75],
    [1, "INFOSYS", "2024-06-22", "BUY", 12, 1555.75],
    [1, "SBI", "2024-06-23", "BUY", 25, 635.40]
]

transactions_df = pd.DataFrame(
    transactions_data,
    columns=["userid", "stockname", "date", "action", "quantity", "price"]
)

transactions_df["date"] = pd.to_datetime(transactions_df["date"])

df=pd.read_csv("stocks_df_ready.csv")
# stocks_df = pd.DataFrame([
#     {"stockname": "VIPCLOTHNG", "companyname": "VIP Clothing Limited", "sector": "Textiles", "market_cap_bucket": "small", "PE": 40.5, "sentiment": 0.05, "price": 700.49},
#     {"stockname": "SHREECEM", "companyname": "SHREE CEMENT LIMITED", "sector": "Cement", "market_cap_bucket": "large", "PE": 39.0, "sentiment": 0.07, "price": 26000.0},
#     {"stockname": "UCAL", "companyname": "UCAL LIMITED", "sector": "Automobile (Tyres)", "market_cap_bucket": "mid", "PE": 14.0, "sentiment": -0.02, "price": 120.0},
#     {"stockname": "INFY", "companyname": "Infosys Ltd", "sector": "IT Services", "market_cap_bucket": "large", "PE": 25.0, "sentiment": 0.12, "price": 1550.0},
#     {"stockname": "RELIANCE", "companyname": "Reliance Industries Ltd", "sector": "Energy", "market_cap_bucket": "large", "PE": 28.0, "sentiment": 0.10, "price": 2700.0},
# ])
stocks_df=df
top5 = recommend_top_stocks(transactions_df, stocks_df, top_n=5)
print("Top Recommendations:")
print(top5)
