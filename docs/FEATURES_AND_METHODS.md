# 特徴量と統計手法（開発者向けサマリ）

## 概要
このドキュメントは、リポジトリ内で実際にコードが生成・利用している特徴量（features）と統計手法（models / evaluation）を開発者向けにまとめたものです。実装の参照先も併記しています。

## データソース
- 電力実績データ: ローカル CSV（日本向けフォーマット） — 実装: [src/data/load_power.py](src/data/load_power.py)
- 気象データ: Open-Meteo 等から取得する時系列（hourly） — 実装: [src/data/fetch_weather.py](src/data/fetch_weather.py)

## 主な前処理と結合
- 時刻の正規化とタイムゾーン: Asia/Tokyo に統一（`load_clean_power_data`, `fetch_weather_open_meteo`）
- power と weather の近接結合: `pd.merge_asof(..., tolerance=...)` を用いて最も近い気象観測を結合（実装: [src/features/build_features.py](src/features/build_features.py) の `merge_tolerance_minutes` 引数）

## 使用している特徴量（feature）
以下は `src/features/build_features.py` で自動的に作成される／期待される主な列です。
- 時刻ベース
  - `hour`：時刻の時間成分（0-23）
  - `dayofweek`：曜日（0=月曜）
  - `is_weekend`：週末フラグ（5,6 -> 1）
- ラグ特徴量（過去の値）
  - `lag_1`, `lag_24`, `lag_168`（デフォルト）など — `add_lags` パラメータで指定
- 移動平均（平滑化）
  - `ma_3`, `ma_24`（デフォルト）など — `add_moving_averages` で指定
- 気象変数（weather_vars の既定）
  - `temperature_2m`, `relativehumidity_2m`, `precipitation`（Open-Meteo の hourly 変数を想定）
- 入力想定の列（ロード処理が整えるカラム名）
  - `power`, `predicted_power`, `usage_rate`, `capacity`（`load_clean_power_data` が日本語ヘッダからマップ）

備考: これらは数値化（`pd.to_numeric(..., errors='coerce')`）され、時刻列は DatetimeIndex（tz-aware）に変換されます。

## 統計手法 / モデル実装（コード参照）

- ARIMA（時系列モデル）
  - 実装: [src/models/arima.py](src/models/arima.py)
  - ライブラリ: `statsmodels`（`sm.tsa.ARIMA`）
  - 用途: 単変量時系列の自己回帰・差分・移動平均モデル。引数 `order=(p,d,q)` を与えて適合。

- 線形回帰（教師あり回帰）
  - 実装: [src/models/regression.py](src/models/regression.py)
  - ライブラリ: `scikit-learn` の `LinearRegression`
  - 用途: ラグや時間特徴、気象変数などの説明変数で `power` を回帰。

- ベースライン回帰（学習・検証分割）
  - 実装: [src/models/baseline_regression.py](src/models/baseline_regression.py)
  - 特記事項: 時系列順に最初の75%を訓練、最後の25%をテストに分割して性能指標を算出する簡易パイプライン
  - 出力: 学習済みモデルと `mae`, `mse` 等のメトリクスを辞書で返す

- ベイズ回帰（MCMC）
  - 実装: [src/models/bayesian.py](src/models/bayesian.py)
  - ライブラリ: `pymc`（PyMC）と `arviz` を利用した事後分布サンプリング
  - 用途: 回帰係数の分布推定や不確実性評価

## 評価指標（evaluation）
- 実装: [src/evaluation/metrics.py](src/evaluation/metrics.py)
- 提供される指標
  - `mae(y_true, y_pred)`：平均絶対誤差
  - `mse(y_true, y_pred)`：平均二乗誤差
- 他: `baseline_regression.py` 内では `sklearn.metrics.mean_absolute_error` と `mean_squared_error` を用いている

## パラメータ／デフォルト値（参照）
- `build_features()` の主な引数
  - `merge_tolerance_minutes`: 既定 30 分（気象観測との結合許容幅）
  - `add_lags`: デフォルト `(1, 24, 168)`（時間単位のラグ）
  - `add_moving_averages`: デフォルト `(3, 24)`
  - `add_time_features`: デフォルト True

## 使い方／実行例（開発者向け）
1. 電力データを読み込む: `from src.data.load_power import load_clean_power_data`
2. 気象データを取得/読み込む: `from src.data.fetch_weather import fetch_weather`
3. 特徴量作成: `from src.features.build_features import build_features`
   - 例: `build_features(power_df, weather_df, add_lags=(1,24), add_moving_averages=(24,))`
4. モデル学習: 目的に応じて `src/models/*.py` を利用

## 参照実装ファイル
- 特徴量構築: [src/features/build_features.py](src/features/build_features.py)
- 電力データロード: [src/data/load_power.py](src/data/load_power.py)
- 気象取得: [src/data/fetch_weather.py](src/data/fetch_weather.py)
- モデル: [src/models/arima.py](src/models/arima.py), [src/models/regression.py](src/models/regression.py), [src/models/baseline_regression.py](src/models/baseline_regression.py), [src/models/bayesian.py](src/models/bayesian.py)
- 評価: [src/evaluation/metrics.py](src/evaluation/metrics.py)

## 追加メモ / 注意点
- 欠損値処理: `build_features` は数値変換で `NaN` を生成し得るため、学習前に行う欠損処理（前方/後方埋め、行削除など）を検討してください。
- 時系列分割: 時系列の順序を保持したまま分割する必要があります（`baseline_regression.py` 参照）。
- 外部データの同期: 気象データと電力データはタイムスタンプ基準で近接結合しており、`merge_tolerance_minutes` により結合精度が影響されます。

---
作成: 自動生成ドキュメント（`docs/FEATURES_AND_METHODS.md`）
