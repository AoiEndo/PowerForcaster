"""Example runner: load power + weather, build features, train baseline model."""
from src.data.load_power import load_clean_power_data
from src.data.fetch_weather import fetch_weather
from src.features.build_features import build_features
from src.models.baseline_regression import train_baseline

def main():
    power = load_clean_power_data("src/data/raw/202603_power_usage/20260327_power_usage.csv")
    weather = fetch_weather(past_days=1)
    df = build_features(power, weather)
    # choose features present
    feature_cols = [c for c in ["temperature_2m", "relativehumidity_2m", "precipitation"] if c in df.columns]
    model, metrics = train_baseline(df, feature_cols)
    print("Trained baseline. Metrics:", metrics)

if __name__ == "__main__":
    main()
