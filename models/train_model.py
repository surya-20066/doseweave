"""
MediSafe AI - Machine Learning Model Training Pipeline
Trains, benchmarks, and evaluates Logistic Regression, Random Forest, and XGBoost classifiers.
Selects the best model based on macro F1-score and saves weights, preprocessor, and performance metrics.
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score
from models.feature_engineering import prepare_train_test_data, get_feature_names
from models.risk_model import get_candidate_models
from utils.logging_config import logger

SAVED_DIR = os.path.join(os.path.dirname(__file__), "saved")
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed", "medication_risk_dataset.csv")

def train_and_evaluate():
    logger.info("Starting MediSafe AI Model Training Pipeline...")

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}. Please run data/generate_training_dataset.py first.")

    df = pd.read_csv(DATASET_PATH)
    logger.info(f"Loaded dataset with shape: {df.shape}")

    X_train, X_test, y_train, y_test, preprocessor = prepare_train_test_data(df)
    feature_names = get_feature_names(preprocessor)

    candidates = get_candidate_models(random_state=42)
    results = {}
    best_model_name = None
    best_f1 = -1.0
    best_model_obj = None

    print("\n" + "="*60)
    print("      MEDISAFE AI - MODEL BENCHMARK & EVALUATION")
    print("="*60)

    for name, model in candidates.items():
        print(f"\nEvaluating {name}...")

        # 5-fold Stratified Cross-Validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1)

        # Fit on full training split
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, average="macro"))
        rec = float(recall_score(y_test, y_pred, average="macro"))
        f1 = float(f1_score(y_test, y_pred, average="macro"))
        cm = confusion_matrix(y_test, y_pred).tolist()
        report = classification_report(y_test, y_pred, target_names=["LOW RISK", "MODERATE RISK", "HIGH RISK"], output_dict=True)

        results[name] = {
            "cv_f1_macro_mean": float(np.mean(cv_scores)),
            "cv_f1_macro_std": float(np.std(cv_scores)),
            "test_accuracy": acc,
            "test_precision_macro": prec,
            "test_recall_macro": rec,
            "test_f1_macro": f1,
            "confusion_matrix": cm,
            "classification_report": report
        }

        print(f"-> Test Accuracy:        {acc:.4f}")
        print(f"-> Test Macro Precision: {prec:.4f}")
        print(f"-> Test Macro Recall:    {rec:.4f}")
        print(f"-> Test Macro F1-Score:  {f1:.4f}")
        print(f"-> 5-Fold CV F1-Macro:   {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model_obj = model

    print("\n" + "="*60)
    print(f"SELECTED BEST MODEL: {best_model_name} (Macro F1: {best_f1:.4f})")
    print("="*60)

    # Save Best Model Artifacts
    os.makedirs(SAVED_DIR, exist_ok=True)
    model_save_path = os.path.join(SAVED_DIR, "risk_model.pkl")
    metrics_save_path = os.path.join(SAVED_DIR, "model_metrics.json")

    joblib.dump(best_model_obj, model_save_path)
    logger.info(f"Saved best model ({best_model_name}) to {model_save_path}")

    # Compute Feature Importances if supported
    feature_importances = {}
    if hasattr(best_model_obj, "feature_importances_"):
        raw_importances = best_model_obj.feature_importances_
        for f_name, imp in zip(feature_names, raw_importances):
            feature_importances[f_name] = float(imp)
    elif hasattr(best_model_obj, "coef_"):
        coef_abs = np.mean(np.abs(best_model_obj.coef_), axis=0)
        for f_name, imp in zip(feature_names, coef_abs):
            feature_importances[f_name] = float(imp)

    # Sort feature importances
    sorted_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

    payload = {
        "best_model": best_model_name,
        "best_f1_macro": best_f1,
        "candidates": results,
        "feature_names": feature_names,
        "top_feature_importances": sorted_importances,
        "target_classes": {
            "0": "LOW RISK",
            "1": "MODERATE RISK",
            "2": "HIGH RISK"
        },
        "dataset_metadata": {
            "samples": len(df),
            "source": "FDA FAERS & SIDER hybrid derived clinical rules with synthetic controlled scenarios"
        }
    }

    with open(metrics_save_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info(f"Saved evaluation metrics and feature importances to {metrics_save_path}")
    print(f"Successfully trained and serialized model artifacts into {SAVED_DIR}\n")
    return payload

if __name__ == "__main__":
    train_and_evaluate()
