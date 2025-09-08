# prepare_stocks_df.py
import pandas as pd
import numpy as np
import random

def prepare_stocks_df(csv_path, output_path="stocks_df_ready.csv"):
    # 1. Load raw NSE stock list
    df = pd.read_csv(csv_path)

    # 2. Clean & rename essential columns
    df = df.rename(columns={
        "SYMBOL": "stockname",
        "NAME OF COMPANY": "companyname",
        "FACE VALUE":"price"
    })

    # Keep only what we need
    df = df[["stockname", "companyname"]].drop_duplicates()

    # 3. Add mock/enriched features (for demo)
    sectors = ["Finance", "IT", "Pharma", "Energy", "Automobile", "Cement", "Textiles", "Chemicals", "Industrial"]
    market_caps = ["small", "mid", "large"]

    df["sector"] = [random.choice(sectors) for _ in range(len(df))]
    df["market_cap_bucket"] = [random.choice(market_caps) for _ in range(len(df))]
    df["PE"] = np.round(np.random.uniform(5, 60, len(df)), 2)   # random PE ratio between 5–60
    df["sentiment"] = np.round(np.random.uniform(-0.1, 0.1, len(df)), 2)  # random sentiment score
    np.random.seed(42)  # so results are consistent across runs
    df["price"] = np.random.uniform(50, 5000, size=2115).round(2)
    # 4. Save to new CSV (ready for recommender)
    df.to_csv(output_path, index=False)
    print(f"[✅] stocks_df saved to {output_path}")
    return df


if __name__ == "__main__":
    # Example usage
    stocks_df = prepare_stocks_df("stock_list.csv")
    print(stocks_df.head(10))
