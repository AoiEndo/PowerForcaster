"""Example runner: load power + weather, build features, train baseline model."""
from src.data.load_power import load_clean_power_data, load_all_power_data
from src.data.fetch_weather import fetch_weather
from src.features.build_features import build_features
from src.models.baseline_regression import train_baseline
import glob
import pandas as pd


def main():
    # ディレクトリ内の全CSVを読み込んで正規化・結合する
    power = load_all_power_data('src/data/raw')
    print('total power rows:', len(power))

    # 気象データは対象期間に合わせて十分な履歴を取得
    weather = fetch_weather(past_days=7)
    df = build_features(power, weather)
    # choose features present
    feature_cols = [c for c in ["temperature_2m", "relativehumidity_2m", "precipitation"] if c in df.columns]
    model, metrics = train_baseline(df, feature_cols)
    print("Trained baseline. Metrics:", metrics)


if __name__ == "__main__":
    main()
