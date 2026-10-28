import csv
import pickle
from pathlib import Path

from sklearn.linear_model import LogisticRegression

DATA_FILE = Path(__file__).with_name("city_data.csv")
MODEL_FILE = Path(__file__).with_name("city_model.pkl")

FEATURES = [
    "rainfall",
    "traffic",
    "road_age",
    "complaints",
    "maintenance_gap",
]

SCALES = [150.0, 100.0, 15.0, 20.0, 20.0]


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "city_data.csv missing! Add your real dataset first."
        )

    X = []
    y = []

    with DATA_FILE.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = FEATURES + ["risk_label"]
        if not reader.fieldnames or not all(
            col in reader.fieldnames for col in required
        ):
            raise ValueError(
                "CSV columns must be: "
                + ", ".join(required)
            )

        for row in reader:
            values = [float(row[col]) for col in FEATURES]
            label = int(row["risk_label"])

            if label not in (0, 1):
                raise ValueError("risk_label must be 0 or 1")

            X.append([
                value / scale
                for value, scale in zip(values, SCALES)
            ])
            y.append(label)

    if len(X) < 10 or len(set(y)) != 2:
        raise ValueError(
            "Need at least 10 real records with both risk labels: 0 and 1."
        )

    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)

    saved_model = {
        "weights": model.coef_[0].tolist(),
        "bias": float(model.intercept_[0]),
    }

    with MODEL_FILE.open("wb") as f:
        pickle.dump(saved_model, f)

    print("Model trained successfully!")
    print("Created:", MODEL_FILE.name)


if __name__ == "__main__":
    main()
