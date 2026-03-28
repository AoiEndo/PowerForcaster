"""Simple regression model wrapper using scikit-learn."""
from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np

class RegressionModel:
    def __init__(self):
        self.model = LinearRegression()

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)
