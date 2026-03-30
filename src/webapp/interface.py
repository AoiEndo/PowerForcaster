"""Web-app interface adapters for PowerForcaster.

Provides thin adapter functions that the web UI can import to load data
and render plots using existing code in `src.data` and `src.visualization`.
"""
from typing import List, Optional
import pandas as pd

from src.data.load_power import load_all_power_data
from src.visualization.plot import plot_series


def load_power(root_dir: Optional[str] = None) -> pd.DataFrame:
    """Load all power data using existing loader.

    Returns a DataFrame indexed by timezone-aware DatetimeIndex (Asia/Tokyo)
    with numeric columns like `power`, `predicted_power`, etc.
    """
    if root_dir is None:
        root_dir = "src/data"
    return load_all_power_data(root_dir)


def numeric_columns(df: pd.DataFrame) -> List[str]:
    """Return numeric columns available for plotting."""
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def plot_column_figure(df: pd.DataFrame, column: str, start_date=None, end_date=None):
    """Filter dataframe by optional date range and return a Matplotlib Figure for the column.

    The returned object is a Matplotlib Figure (suitable for Streamlit's `st.pyplot`).
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty")

    # filter by date if provided (dates can be date or datetime)
    df_work = df
    try:
        idx_dates = df_work.index.date
    except Exception:
        # if index isn't datetime-like, try to parse
        df_work = df_work.copy()
        if "time" in df_work.columns:
            df_work = df_work.set_index(pd.to_datetime(df_work["time"]))
        idx_dates = df_work.index.date

    if start_date is not None:
        df_work = df_work[df_work.index.date >= pd.to_datetime(start_date).date()]
    if end_date is not None:
        df_work = df_work[df_work.index.date <= pd.to_datetime(end_date).date()]

    if column not in df_work.columns:
        raise KeyError(f"Column not found: {column}")

    # prepare dataframe for plotting helper: make time column
    df_plot = df_work.reset_index()
    # ensure column name of time is 'time'
    if df_plot.columns[0].lower() != "time":
        df_plot = df_plot.rename(columns={df_plot.columns[0]: "time"})

    ax = plot_series(df_plot, time_col="time", value_col=column, title=column)
    fig = ax.get_figure()
    return fig
