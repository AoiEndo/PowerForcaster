"""Simple Streamlit app to explore power time series.

Run with: `streamlit run webapp/streamlit_app.py`
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Ensure repository root is on sys.path so `from src...` works in hosted runtimes
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.webapp.interface import load_power, numeric_columns, plot_column_figure


st.set_page_config(page_title="PowerForcaster Explorer", layout="wide")

st.sidebar.title("Settings")
root_dir = st.sidebar.text_input("Data root directory", value="src/data/raw")

@st.cache_data(ttl=300)
def _load(root):
    return load_power(root)


df = _load(root_dir)

st.title("PowerForcaster — Explorer")

if df is None or df.empty:
    st.warning("データが見つかりません。`src/data/raw` に CSV があるか確認してください。")
else:
    st.sidebar.markdown("**Visualization**")
    cols = numeric_columns(df)
    default = "power" if "power" in cols else (cols[0] if cols else None)
    selected_col = st.sidebar.selectbox("Select column to plot", options=cols, index=cols.index(default) if default in cols else 0)

    # date range
    min_date = df.index.date.min()
    max_date = df.index.date.max()
    start_date, end_date = st.sidebar.date_input("Date range", value=[min_date, max_date])

    # render plot
    try:
        fig = plot_column_figure(df, selected_col, start_date=start_date, end_date=end_date)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"プロット中にエラー: {e}")

    # show raw table toggle
    if st.sidebar.checkbox("Show data table"):
        st.dataframe(df.reset_index().head(500))
