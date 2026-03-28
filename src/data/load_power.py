"""Load power consumption data utilities."""
import pandas as pd

def load_power_csv(path: str, parse_dates=None) -> pd.DataFrame:
    """Load power consumption CSV into DataFrame."""
    df = pd.read_csv(path, parse_dates=parse_dates)
    return df
