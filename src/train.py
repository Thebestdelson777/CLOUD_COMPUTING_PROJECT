import argparse
import os
import time
import joblib
import mlflow
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data", type=str, required=True, help="Path to curated selected_features.csv")
    parser.add_argument("--output", type=str, required=True, help="Output directory for saved model")

    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--val_size", type=float, default=0.2)
    parser.add_argument("--random_seed", type=int, default=42)

    parser.add_argument("--n_estimators", type=int, default=200)
    parser.add_argument("--max_depth", type=int, default=12)
    parser.add_argument("--min_samples_split", type=int, default=2)
    parser.add_argument("--min_samples_leaf", type=int, default=1)

    return parser.parse_args()


def evaluate_model(model, x, y, split_name):
    preds = model.predict(x)

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(x)[:, 1]
    else:
        probs = preds

    acc = accuracy_score(y, preds)
    prec = precision_score(y, preds, zero_division=0)
    rec = recall_score(y, preds, zero_division=0)
    f1 = f1_score(y, preds, zero_division=0)

    try:
        auc = roc_auc_score(y, probs)
    except Exception:
        auc = 0.0

    cm = confusion_matrix(y, preds)

    mlflow.log_metric(f"{split_name}_accuracy", acc)
    mlflow.log_metric(f"{split_name}_precision", prec)
    mlflow.log_metric(f"{split_name}_recall", rec)
    mlflow.log_metric(f"{split_name}_f1", f1)
    mlflow.log_metric(f"{split_name}_auc", auc)

    print(f"\n{split_name.upper()} METRICS")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1       : {f1:.4f}")
    print(f"AUC      : {auc:.4f}")
    print("Confusion Matrix:")
    print(cm)

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "auc": auc
    }


def main():
    args = parse_args()
    start_time = time.time()

    print("Loading curated dataset...")
    df = pd.read_csv(args.data)

    if "Label" not in df.columns:
        raise ValueError("Target column 'Label' not found in dataset.")

    x = df.drop(columns=["Label"])
    y = df["Label"]

    print("Dataset shape:", df.shape)
    print("Feature matrix shape:", x.shape)

    # Train/temp split
    x_train, x_temp, y_train, y_temp = train_test_split(
        x,
        y,
        test_size=args.test_size + args.val_size,
        random_state=args.random_seed,
        stratify=y
    )

    # Validation/test split
    relative_val_size = args.val_size / (args.test_size + args.val_size)

    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=(1 - relative_val_size),
        random_state=args.random_seed,
        stratify=y_temp
    )

    print("Train shape:", x_train.shape)
    print("Validation shape:", x_val.shape)
    print("Test shape:", x_test.shape)

    mlflow.log_param("random_seed", args.random_seed)
    mlflow.log_param("test_size", args.test_size)
    mlflow.log_param("val_size", args.val_size)
    mlflow.log_param("n_estimators", args.n_estimators)
    mlflow.log_param("max_depth", args.max_depth)
    mlflow.log_param("min_samples_split", args.min_samples_split)
    mlflow.log_param("min_samples_leaf", args.min_samples_leaf)
    mlflow.log_param("feature_count", x.shape[1])

    # Baseline model
    print("\nTraining baseline model...")
    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(x_train, y_train)

    baseline_metrics = evaluate_model(baseline, x_test, y_test, "baseline_test")
    mlflow.log_metric("baseline_test_accuracy_final", baseline_metrics["accuracy"])
    mlflow.log_metric("baseline_test_f1_final", baseline_metrics["f1"])

    # Main model
    print("\nTraining RandomForest model...")
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_split=args.min_samples_split,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.random_seed,
        n_jobs=-1
    )
    model.fit(x_train, y_train)

    evaluate_model(model, x_train, y_train, "train")
    val_metrics = evaluate_model(model, x_val, y_val, "val")
    test_metrics = evaluate_model(model, x_test, y_test, "test")

    mlflow.log_metric("final_val_accuracy", val_metrics["accuracy"])
    mlflow.log_metric("final_val_f1", val_metrics["f1"])
    mlflow.log_metric("final_test_accuracy", test_metrics["accuracy"])
    mlflow.log_metric("final_test_f1", test_metrics["f1"])

    print("\nSaving model artifacts...")
    os.makedirs(args.output, exist_ok=True)

    model_path = os.path.join(args.output, "model.pkl")
    features_path = os.path.join(args.output, "feature_columns.pkl")

    joblib.dump(model, model_path)
    joblib.dump(list(x.columns), features_path)

    mlflow.log_artifact(model_path)
    mlflow.log_artifact(features_path)

    runtime = time.time() - start_time
    mlflow.log_metric("training_runtime_seconds", runtime)

    print(f"\nTraining complete in {runtime:.2f} seconds")
    print("Saved:")
    print("-", model_path)
    print("-", features_path)


if __name__ == "__main__":
    main()
