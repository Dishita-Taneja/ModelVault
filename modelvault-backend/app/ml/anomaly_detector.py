
import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    def __init__(self, contamination: float = 0.33, n_estimators: int = 100, random_state: int = 42):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=1
        )
        self.threshold = 0.5
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> "AnomalyDetector":
        self.model.fit(X)
        raw_scores = -self.model.score_samples(X)  # Higher raw_score = more anomalous
        
        # Calculate decision threshold based on contamination quantile
        if len(raw_scores) > 0:
            self.threshold = float(np.quantile(raw_scores, 1.0 - self.contamination))
        else:
            self.threshold = 0.5

        self.is_fitted = True
        return self

    def predict_scores(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("AnomalyDetector must be fitted before calling predict_scores.")
        
        raw_scores = -self.model.score_samples(X)
        # Min-Max normalize scores to [0.0, 1.0] range
        min_s = float(np.min(raw_scores)) if len(raw_scores) > 0 else 0.0
        max_s = float(np.max(raw_scores)) if len(raw_scores) > 0 else 1.0
        denom = (max_s - min_s) if (max_s - min_s) > 1e-6 else 1.0
        
        norm_scores = (raw_scores - min_s) / denom
        return norm_scores

    def predict_anomalies(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        norm_scores = self.predict_scores(X)
        # Flag as anomaly if normalized score >= 0.70 or raw_score >= threshold
        anomalies = norm_scores >= 0.65
        return norm_scores, anomalies
