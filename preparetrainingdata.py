import pandas as pd
import random
from faker import Faker
import numpy as np

# -----------------------------
# 1️⃣ Generate Fake Transactions
# -----------------------------
def faketransaction():
    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    # Config
    num_users = 40
    transactions_per_user = 15
    n_selected_stocks = 250  # number of stocks to sample

    # Load stock list
    stock_df = pd.read_csv("stock_list.csv")
    selected_stocks = stock_df.sample(n=n_selected_stocks, random_state=42)
    stocks = dict(zip(selected_stocks["SYMBOL"], selected_stocks["NAME OF COMPANY"]))

    data = []
    for user_id in range(1, num_users + 1):
        portfolio_id = user_id
        for _ in range(transactions_per_user):
            stock_symbol = random.choice(list(stocks.keys()))
            company_name = stocks[stock_symbol]

            quantity = random.randint(1, 50)
            price = round(random.uniform(50, 5000), 2)
            transaction_type = random.choices(['buy', 'sell'], weights=[0.7, 0.3])[0]
            timestamp = fake.date_time_between(start_date='-1y', end_date='now')

            data.append({
                'transactionid': None,
                'userid': user_id,
                'portfolioid': portfolio_id,
                'companyname': company_name,
                'stockname': stock_symbol,
                'quantity': quantity,
                'price': price,
                'transactiontype': transaction_type,
                'timestamp': timestamp
            })

    transactions_df = pd.DataFrame(data)
    transactions_df.to_csv("transactions.csv", index=False)
    print("✅ 'transactions.csv' created")
    print(transactions_df.head())

# -----------------------------
# 2️⃣ Add Technical Indicators
# -----------------------------
def add_technical_indicators(df):
    df = df.sort_values('timestamp')
    
    # Moving averages
    df['ma5'] = df.groupby('stockname')['price'].transform(lambda x: x.rolling(5, min_periods=1).mean())
    df['ma10'] = df.groupby('stockname')['price'].transform(lambda x: x.rolling(10, min_periods=1).mean())
    df['ma20'] = df.groupby('stockname')['price'].transform(lambda x: x.rolling(20, min_periods=1).mean())
    
    # Volatility & avg returns
    df['volatility'] = df.groupby('stockname')['price'].transform(lambda x: x.rolling(10, min_periods=1).std())
    df['avg_return'] = df.groupby('stockname')['price'].transform(lambda x: x.pct_change().rolling(10, min_periods=1).mean())
    
    df.fillna(0, inplace=True)
    return df

# -----------------------------
# 3️⃣ Prepare Training Dataset
# -----------------------------
def make_training_dataset():
    # Load CSVs
    transactions = pd.read_csv("transactions.csv")
    stocks = pd.read_csv("stocks.csv")

    # Merge transactions with stock features
    data = transactions.merge(stocks, on='stockname', how='left')

    # Convert timestamp to datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data['day_of_week'] = data['timestamp'].dt.dayofweek
    data['month'] = data['timestamp'].dt.month

    # Add technical indicators
    data = add_technical_indicators(data)

    # --- User-level aggregate features ---
    user_agg = transactions.groupby('userid').agg(
        user_total_transactions=('stockname', 'count'),
        user_avg_quantity=('quantity', 'mean'),
        user_avg_value=('quantity', lambda x: np.mean(x * data.loc[x.index, 'price']))
    ).reset_index()
    data = data.merge(user_agg, on='userid', how='left')

    # --- Stock-level aggregate features ---
    stock_agg = transactions.groupby('stockname').agg(
        stock_total_transactions=('userid', 'count'),
        stock_avg_quantity=('quantity', 'mean')
    ).reset_index()
    data = data.merge(stock_agg, on='stockname', how='left')

    # --- Encode categorical features ---
    categorical_cols = ['sector', 'market_cap_bucket']
    data = pd.get_dummies(data, columns=categorical_cols)

    # --- Target variable ---
    data['target'] = data['transactiontype'].apply(lambda x: 1 if x.lower() == 'buy' else 0)

    # --- Save full dataset for inspection ---
    data.to_csv("training_data.csv", index=False)
    print(f"✅ training_data.csv created: {data.shape[0]} rows, {data.shape[1]} cols")

    # --- ML-ready dataset ---
    drop_cols = [
        'transactionid', 'userid', 'portfolioid',
        'companyname', 'stockname', 'transactiontype',
        'timestamp'
    ]
    X = data.drop(columns=drop_cols + ['target'], errors='ignore')
    y = data['target']

    np.save("X.npy", X.values)
    np.save("y.npy", y.values)
    print(f"✅ ML dataset ready: X={X.shape}, y={y.shape}")

# -----------------------------
# Execute
# -----------------------------
#faketransaction()
make_training_dataset()
