import pandas as pd


def build_features(power_df: pd.DataFrame, weather_df: pd.DataFrame,
                   weather_vars=None, merge_tolerance_minutes: int = 30) -> pd.DataFrame:
    """Merge power and weather into a single feature DataFrame.

    - `power_df` is expected to have a DatetimeIndex (tz-aware) or a `time` column.
    - `weather_df` is expected to have a `time` column (datetime-like) and weather vars.
    - Returns a DataFrame indexed by time with numeric feature columns.
    """
    if weather_vars is None:
        weather_vars = ["temperature_2m", "relativehumidity_2m", "precipitation"]

    pw = power_df.copy()
    # ensure time column exists on both sides for merge_asof
    if isinstance(pw.index, pd.DatetimeIndex):
        if pw.index.name != "time":
            pw = pw.rename_axis("time")
        pw = pw.reset_index()
    else:
        if "time" not in pw.columns:
            raise ValueError("power_df must have a DatetimeIndex or a 'time' column")
        pw["time"] = pd.to_datetime(pw["time"]) 

    w = weather_df.copy()
    if "time" not in w.columns:
        raise ValueError("weather_df must contain a 'time' column")
    w["time"] = pd.to_datetime(w["time"]) 

    # normalize tz to Asia/Tokyo for both
    try:
        if w["time"].dt.tz is None:
            w["time"] = w["time"].dt.tz_localize("Asia/Tokyo")
        else:
            w["time"] = w["time"].dt.tz_convert("Asia/Tokyo")
    except Exception:
        w["time"] = pd.to_datetime(w["time"]).dt.tz_localize("Asia/Tokyo")

    try:
        if pw["time"].dt.tz is None:
            pw["time"] = pw["time"].dt.tz_localize("Asia/Tokyo")
        else:
            pw["time"] = pw["time"].dt.tz_convert("Asia/Tokyo")
    except Exception:
        pw["time"] = pd.to_datetime(pw["time"]).dt.tz_localize("Asia/Tokyo")

    # select weather vars, drop NA times
    wsel = w[["time"] + [c for c in weather_vars if c in w.columns]].drop_duplicates("time").sort_values("time")
    pw = pw.sort_values("time")

    # merge_asof to align nearest weather observation within tolerance
    merged = pd.merge_asof(pw, wsel, on="time", direction="nearest",
                           tolerance=pd.Timedelta(f"{merge_tolerance_minutes}min"))

    # Ensure numeric conversion
    for c in ["power", "predicted_power", "usage_rate", "capacity"] + weather_vars:
        if c in merged.columns:
            merged[c] = pd.to_numeric(merged[c], errors="coerce")

    # set time index
    merged = merged.set_index("time")
    return merged

