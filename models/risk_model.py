"""
MediSafe AI - Risk Classifier Definitions
Wraps model configurations for Logistic Regression, Random Forest, and XGBoost.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

def get_candidate_models(random_state: int = 42):
    """Returns candidate estimators dictionary for benchmark and cross-validation."""
    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        )
    }

    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=180,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.85,
            eval_metric="mlogloss",
            random_state=random_state
        )
    except ImportError:
        pass

    return models
