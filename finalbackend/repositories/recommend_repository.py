import pickle
import os
from typing import Any

class RecommendRepository:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), "..", "recml_xgb.pkl")
        self.train_cols_path = os.path.join(os.path.dirname(__file__), "..", "training_columns.pkl")
        self.model = self._load_pickle(self.model_path)
        self.train_cols = self._load_pickle(self.train_cols_path)

    def _load_pickle(self, path: str) -> Any:
        with open(path, "rb") as f:
            return pickle.load(f)
