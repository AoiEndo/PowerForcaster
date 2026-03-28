"""ARIMA model stub (uses statsmodels)."""
import statsmodels.api as sm
import pandas as pd

def fit_arima(series: pd.Series, order=(1,0,0)):
    model = sm.tsa.ARIMA(series, order=order)
    res = model.fit()
    return res
