import json
import os
import joblib
import pandas as pd

model = None
feature_columns = None


def init():
    global model, feature_columns

    model_dir = os.getenv("AZUREML_MODEL_DIR")
    print("AZUREML_MODEL_DIR:", model_dir)

    model_path = None
    features_path = None

    for root, dirs, files in os.walk(model_dir):
        print("Scanning:", root, files)
        if "model.pkl" in files:
            model_path = os.path.join(root, "model.pkl")
        if "feature_columns.pkl" in files:
            features_path = os.path.join(root, "feature_columns.pkl")

    if model_path is None:
        raise FileNotFoundError("model.pkl not found inside AZUREML_MODEL_DIR")
    if features_path is None:
        raise FileNotFoundError("feature_columns.pkl not found inside AZUREML_MODEL_DIR")

    model = joblib.load(model_path)
    feature_columns = joblib.load(features_path)

    print("Model loaded from:", model_path)
    print("Feature columns loaded from:", features_path)
    print("Expected feature count:", len(feature_columns))


def run(raw_data):
    try:
        data = json.loads(raw_data)
        records = data["data"] if isinstance(data, dict) and "data" in data else data
        df = pd.DataFrame(records)

        missing_cols = [col for col in feature_columns if col not in df.columns]
        if missing_cols:
            return {"error": f"Missing feature columns: {missing_cols}"}

        df = df[feature_columns]

        preds = model.predict(df)

        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(df)[:, 1].tolist()
        else:
            probs = [None] * len(preds)

        return {
            "predictions": preds.tolist(),
            "probabilities": probs
        }

    except Exception as e:
        return {"error": str(e)}