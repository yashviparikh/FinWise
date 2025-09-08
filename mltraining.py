# mltraining.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# 1. Load data
df = pd.read_csv("training_data.csv")

# 2. Drop non-feature columns (identifiers, names)
drop_cols = [
    "transactionid", "companyname", "stockname",
    "transactiontype", "timestamp", "userid","portfolioid" # these are not numeric features
]
df = df.drop(columns=[c for c in drop_cols if c in df.columns])

# 3. Define features and target
X = df.drop(columns=["target"])
y = df["target"]

# 4. Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.5, random_state=12, stratify=y
)

# 5. Train model
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"   # ✅ Step 1: fix class imbalance
)

model.fit(X_train, y_train)

# 6. Evaluate
y_pred = model.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# --- Feature Importances ---
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]
feature_names = X_train.columns if isinstance(X_train, pd.DataFrame) else range(X_train.shape[1])

print("\nTop 15 Features by Importance:")
for i in range(min(15, len(feature_names))):
    print(f"{i+1}. {feature_names[indices[i]]}: {importances[indices[i]]:.4f}")
# print(y_pred)
# print("Accuracy:", accuracy_score(y_test, y_pred))
# print(classification_report(y_test, y_pred))

# # 7. Save trained model
# joblib.dump(model, "model.pkl")
# print("✅ Model saved as model.pkl")
