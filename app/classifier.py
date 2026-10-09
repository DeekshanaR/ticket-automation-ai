"""AI component 1: ML model that predicts ticket category and priority.

Uses TF-IDF text features + Logistic Regression (scikit-learn).
"""
import logging

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.config import DATA_PATH, MODEL_PATH

log = logging.getLogger(__name__)


def _pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000)),
    ])


def train(csv_path=DATA_PATH, model_path=MODEL_PATH, verbose=True) -> dict:
    """Train category + priority models, print metrics and save to disk."""
    df = pd.read_csv(csv_path)
    text = (df["title"] + " " + df["description"]).tolist()
    models, scores = {}, {}
    for target in ("category", "priority"):
        x_tr, x_te, y_tr, y_te = train_test_split(
            text, df[target], test_size=0.2, random_state=42, stratify=df[target]
        )
        model = _pipeline().fit(x_tr, y_tr)
        pred = model.predict(x_te)
        report = classification_report(y_te, pred, output_dict=True, zero_division=0)
        scores[target] = round(report["accuracy"], 3)
        if verbose:
            print(f"\n=== {target.upper()} model ===")
            print(classification_report(y_te, pred, zero_division=0))
        # Refit on all data for the final saved model.
        models[target] = _pipeline().fit(text, df[target])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(models, model_path)
    log.info("Model saved to %s", model_path)
    return scores


class TicketClassifier:
    def __init__(self, models: dict):
        self.models = models

    def predict(self, title: str, description: str) -> dict:
        text = [f"{title} {description}"]
        cat_model, pri_model = self.models["category"], self.models["priority"]
        cat_proba = cat_model.predict_proba(text)[0]
        pri_proba = pri_model.predict_proba(text)[0]
        return {
            "category": str(cat_model.classes_[cat_proba.argmax()]),
            "priority": str(pri_model.classes_[pri_proba.argmax()]),
            "confidence": round(float(cat_proba.max()), 3),
        }


_classifier = None


def get_classifier() -> TicketClassifier:
    """Load the saved model (training it first if it does not exist yet)."""
    global _classifier
    if _classifier is None:
        if not MODEL_PATH.exists():
            if not DATA_PATH.exists():
                from scripts.generate_data import generate
                generate(DATA_PATH)
            train(verbose=False)
        _classifier = TicketClassifier(joblib.load(MODEL_PATH))
    return _classifier
