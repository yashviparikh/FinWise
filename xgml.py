import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb
from collections import Counter
import pickle

# ----------------------------
# Load data
# ----------------------------
X = np.load("X.npy", allow_pickle=True)
y = np.load("y.npy", allow_pickle=True)

# Convert to DataFrame
training_data = pd.read_csv("training_data.csv")
drop_cols = ['transactionid', 'userid', 'portfolioid', 'companyname', 'stockname',
             'transactiontype', 'timestamp', 'target']
feature_cols = [c for c in training_data.columns if c not in drop_cols]
X = pd.DataFrame(X, columns=feature_cols)

# ----------------------------
# Fix dtypes
# ----------------------------
for col in X.columns:
    # Convert numeric-looking columns to float
    try:
        X[col] = X[col].astype(float)
    except:
        # Convert True/False strings to bool if any
        X[col] = X[col].map({'True': True, 'False': False}).fillna(0).astype(float)

# ----------------------------
# Train-test split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=22, stratify=y
)

# ----------------------------
# Handle class imbalance
# ----------------------------
counter = Counter(y_train)
scale_pos_weight = counter[0] / counter[1]  # ratio of sell/buy

# ----------------------------
# XGBoost model
# ----------------------------
model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric='logloss',
    scale_pos_weight=scale_pos_weight,
    random_state=42
)

# ----------------------------
# Train
# ----------------------------
model.fit(X_train, y_train)

# ----------------------------
# Evaluate
# ----------------------------
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# ----------------------------
# Feature importances
# ----------------------------
importances = dict(zip(X.columns, model.feature_importances_))
sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
print("\nTop 15 Features by Importance:")
for i, (feat, imp) in enumerate(sorted_importances[:15], 1):
    print(f"{i}. {feat}: {imp:.4f}")

# ----------------------------
# Save model
# ----------------------------
with open("recommendation_model_xgb.pkl", "wb") as f:
    pickle.dump(model, f)
print("\n✅ Model saved as recommendation_model_xgb.pkl")
