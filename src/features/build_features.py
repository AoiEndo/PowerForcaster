"""Feature engineering: combine power and weather into modeling features."""
import pandas as pd

def build_features(power_df: pd.DataFrame, weather_df: pd.DataFrame, on="timestamp") -> pd.DataFrame:
    """Merge datasets and create simple time/weather features.

    Expects both DataFrames to have a common datetime column (default `timestamp`).
    """
    df = pd.merge_asof(
        power_df.sort_values(on),
        weather_df.sort_values(on),
        on=on,
        direction="nearest",
        tolerance=pd.Timedelta("1H"),
    )

    # basic features
    df["hour"] = df[on].dt.hour
    df["dayofweek"] = df[on].dt.dayofweek
    if "temperature" in df.columns:
        df["temp_diff_24h"] = df["temperature"] - df["temperature"].shift(24)
    return df
