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
                    return hourly.iloc[:24].reset_index(drop=True)
                return hourly.reset_index(drop=True)

    # 候補が見つからない場合は、従来の全体データを返す（可能なら分が00の行を優先）
    try:
        df["_minute"] = df["time"].dt.minute
        hourly = df[df["_minute"] == 0].copy()
        if not hourly.empty:
            hourly = hourly.sort_values("time").reset_index(drop=True)
            if len(hourly) >= 24:
                return hourly.iloc[:24].reset_index(drop=True)
            return hourly.reset_index(drop=True)
    except Exception:
        pass

    return df.reset_index(drop=True)
