from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import pandas as pd
from typing import Tuple


def train_baseline(df: pd.DataFrame, feature_cols, target_col: str = "power") -> Tuple[LinearRegression, dict]:
    """Train a simple linear regression on provided features and return model + metrics.

    Expects `df` indexed by time and with numeric columns.
    Splits: first 75% train, last 25% test (time-ordered).
    """
    df = df.dropna(subset=[target_col])
    X = df[feature_cols].copy()
    y = df[target_col].copy()

    n = len(df)
    if n < 4:
        raise ValueError("Not enough rows to train/test")
    split = int(n * 0.75)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model = LinearRegression()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    metrics = {
        "mae": float(mean_absolute_error(y_test, preds)),
        "mse": float(mean_squared_error(y_test, preds)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    return model, metrics
