"""Load power consumption data utilities with cleaning for Japanese CSVs."""
import pandas as pd


def load_power_csv(path: str, parse_dates=None) -> pd.DataFrame:
    """Simple CSV loader."""
    return pd.read_csv(path, parse_dates=parse_dates)


def load_clean_power_data(file_path: str) -> pd.DataFrame:
    """Load and clean Japanese power CSV files.

    - Handles Shift-JIS encoding and files with preamble lines.
    - Looks for header line containing: "DATE,TIME,当日実績"
    - Builds a `time` column and renames columns to English keys.
    """
    # 多くの日本のCSVは Shift-JIS だが UTF-8 の場合もある。まず UTF-8 を試し、失敗またはヘッダが見つからなければ Shift-JIS を試す。
    encodings_to_try = ["utf-8", "shift_jis"]
    lines = None
    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc, errors="ignore") as f:
                cand = f.readlines()
            # 先頭数行に目的のヘッダが含まれるか確認
            if any("DATE,TIME,当日実績" in l for l in cand):
                lines = cand
                break
            # もし見つからなくても最初に読み込めていれば保留して後で使う
            if lines is None:
                lines = cand
        except Exception:
            continue

    if lines is None:
        raise ValueError("ファイルを読み取れませんでした: {}".format(file_path))

    # ヘッダ行インデックスをすべて見つけて、セクション毎に解析する
    header_idxs = [i for i, line in enumerate(lines) if "DATE" in line.upper() and "TIME" in line.upper()]
    from io import StringIO

    # 全体を一度読み込んでおく（フォールバック用）
    try:
        df = pd.read_csv(StringIO("".join(lines)))
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
        else:
            if 'DATE' in df.columns and 'TIME' in df.columns:
                df['_DATE_parsed'] = pd.to_datetime(df['DATE'].astype(str), errors='coerce')
                df['_TIME_clean'] = df['TIME'].astype(str).str.extract(r"(\d{1,2}:\d{2})")[0].fillna('00:00')
                df['time'] = pd.to_datetime(df['_DATE_parsed'].dt.strftime('%Y-%m-%d') + ' ' + df['_TIME_clean'])
                df = df.drop(columns=[c for c in ['_DATE_parsed', '_TIME_clean'] if c in df.columns])
    except Exception:
        df = pd.DataFrame()

    candidate_blocks = []
    if header_idxs:
        for idx_i, idx in enumerate(header_idxs):
            next_idx = header_idxs[idx_i + 1] if idx_i + 1 < len(header_idxs) else len(lines)
            block_lines = lines[idx:next_idx]
            try:
                block_df = pd.read_csv(StringIO("".join(block_lines)))
            except Exception:
                continue

            # 列名マッピング
            col_map = {}
            for col in block_df.columns:
                if col.upper() == "DATE":
                    col_map[col] = "DATE"
                elif col.upper() == "TIME":
                    col_map[col] = "TIME"
                elif any(k in col for k in ["当日実績", "実績"]):
                    col_map[col] = "power"
                elif any(k in col for k in ["予測", "予"]):
                    col_map[col] = "predicted_power"
                elif "使用" in col or "使用率" in col:
                    col_map[col] = "usage_rate"
                elif "供給" in col or "供給力" in col:
                    col_map[col] = "capacity"

            if col_map:
                block_df = block_df.rename(columns=col_map)

            # 時刻作成
            if "DATE" in block_df.columns and "TIME" in block_df.columns:
                block_df["_DATE_parsed"] = pd.to_datetime(block_df["DATE"].astype(str), errors="coerce", dayfirst=False)
                block_df["_TIME_clean"] = block_df["TIME"].astype(str).str.extract(r"(\d{1,2}:\d{2})")[0]
                block_df = block_df[~block_df["_DATE_parsed"].isna()].copy()
                if block_df.empty:
                    continue
                block_df["_TIME_clean"] = block_df["_TIME_clean"].fillna("00:00")
                block_df["time"] = pd.to_datetime(block_df["_DATE_parsed"].dt.strftime("%Y-%m-%d") + " " + block_df["_TIME_clean"])
                block_df = block_df.drop(columns=[c for c in ["_DATE_parsed", "_TIME_clean"] if c in block_df.columns])
            elif "time" in block_df.columns:
                block_df["time"] = pd.to_datetime(block_df["time"])
            else:
                continue

            # 必要列だけにする
            keep_cols = [c for c in ["time", "power", "predicted_power", "usage_rate", "capacity"] if c in block_df.columns]
            block_df = block_df[keep_cols]

            # 時刻が 00 分の行を集め、ユニークな時間数を数える
            try:
                bh = block_df[block_df["time"].dt.minute == 0].copy()
                unique_hours = bh["time"].dt.hour.nunique()
            except Exception:
                unique_hours = 0

            candidate_blocks.append((unique_hours, block_df))

    def _finalize_df(df_in):
        """Coerce numeric columns, drop missing 'power', set DatetimeIndex (Asia/Tokyo)."""
        df_work = df_in.copy()
        for c in ["power", "predicted_power", "usage_rate", "capacity"]:
            if c in df_work.columns:
                df_work[c] = pd.to_numeric(df_work[c].astype(str).str.replace(',', ''), errors='coerce')
        # drop rows missing power
        if 'power' in df_work.columns:
            df_work = df_work[~df_work['power'].isna()].copy()
        # ensure time column exists and make it index with timezone
        if 'time' in df_work.columns:
            df_work = df_work.sort_values('time')
            try:
                if df_work['time'].dt.tz is None:
                    df_work['time'] = df_work['time'].dt.tz_localize('Asia/Tokyo')
                else:
                    df_work['time'] = df_work['time'].dt.tz_convert('Asia/Tokyo')
            except Exception:
                df_work['time'] = pd.to_datetime(df_work['time'])
                df_work['time'] = df_work['time'].dt.tz_localize('Asia/Tokyo')
            df_work = df_work.set_index('time')
        return df_work

    # 候補から 24 時間分を持つブロックを優先して選択
    if candidate_blocks:
        # sort by unique_hours desc
        candidate_blocks.sort(key=lambda x: x[0], reverse=True)
        for unique_hours, block_df in candidate_blocks:
            if unique_hours >= 24:
                # 抽出して 24 行にする
                hourly = block_df[block_df["time"].dt.minute == 0].copy()
                hourly = hourly.sort_values("time").reset_index(drop=True)
                # 24以上なら先頭の24を、未満ならそのまま返す
                if len(hourly) >= 24:
                    sel = hourly.iloc[:24].reset_index(drop=True)
                    return _finalize_df(sel)
                return _finalize_df(hourly.reset_index(drop=True))

    # 候補が見つからない場合は、従来の全体データを返す（可能なら分が00の行を優先）
    try:
        df["_minute"] = df["time"].dt.minute
        hourly = df[df["_minute"] == 0].copy()
        if not hourly.empty:
            hourly = hourly.sort_values("time").reset_index(drop=True)
            if len(hourly) >= 24:
                return _finalize_df(hourly.iloc[:24].reset_index(drop=True))
            return _finalize_df(hourly.reset_index(drop=True))
    except Exception:
        pass

    return _finalize_df(df.reset_index(drop=True))


def load_all_power_data(root_dir: str = "src/data/raw") -> pd.DataFrame:
    """Find all CSVs under `root_dir`, load and normalize them into one DataFrame.

    - Uses `load_clean_power_data` for each file, then concatenates results.
    - Ensures a DatetimeIndex with Asia/Tokyo tz, numeric columns coerced, duplicates removed.
    """
    import glob
    import os

    pattern = os.path.join(root_dir, "**", "*.csv")
    files = sorted(glob.glob(pattern, recursive=True))
    parts = []
    for fp in files:
        try:
            p = load_clean_power_data(fp)
            parts.append(p)
        except Exception:
            # skip problematic files
            continue

    if not parts:
        return pd.DataFrame()

    df = pd.concat(parts)

    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            try:
                if df['time'].dt.tz is None:
                    df['time'] = df['time'].dt.tz_localize('Asia/Tokyo')
                else:
                    df['time'] = df['time'].dt.tz_convert('Asia/Tokyo')
            except Exception:
                df['time'] = pd.to_datetime(df['time'])
                df['time'] = df['time'].dt.tz_localize('Asia/Tokyo')
            df = df.set_index('time')

    # Coerce numeric cols
    for c in ['power', 'predicted_power', 'usage_rate', 'capacity']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # drop missing power rows and duplicated timestamps
    if 'power' in df.columns:
        df = df[~df['power'].isna()].copy()
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    return df
