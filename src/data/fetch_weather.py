"""Utilities to fetch weather data (Open-Meteo implementation)."""
import requests
import pandas as pd
from typing import Optional


def fetch_weather_open_meteo(latitude: float = 35.68,
                             longitude: float = 139.76,
                             past_days: int = 30,
                             timezone: str = "Asia/Tokyo") -> pd.DataFrame:
    """Fetch hourly weather data from Open-Meteo and return a DataFrame.

    Returns a DataFrame with a `time` datetime column and requested variables.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join([
            "temperature_2m",
            "relativehumidity_2m",
            "precipitation",
        ]),
        "past_days": past_days,
        "timezone": timezone,
    }

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "hourly" not in data:
        raise ValueError("Open-Meteo response missing 'hourly' key")

    df = pd.DataFrame(data["hourly"])
    t = pd.to_datetime(df["time"]) 
    # normalize timezone-aware or naive timestamps to naive UTC-localized datetimes
    try:
        t = t.dt.tz_convert(None)
    except Exception:
        try:
            t = t.dt.tz_localize(None)
        except Exception:
            t = t.astype("datetime64[ns]")
    df["time"] = t
    return df


def fetch_weather(*args, **kwargs) -> pd.DataFrame:
    """Compatibility wrapper for a simple `fetch_weather()` call."""
    return fetch_weather_open_meteo(*args, **kwargs)


if __name__ == "__main__":
    # quick smoke test when running the module directly
    df = fetch_weather_open_meteo()
    print(df.shape)
    print(df.head().to_string())
