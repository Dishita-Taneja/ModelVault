from typing import Tuple
import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """
    Unsupervised Isolation Forest Anomaly Detector with Normalized Scoring.
    
    Explanation of Scoring Flow:
    1. Isolation Forest Output:
       - model.score_samples(X) returns negative decision path lengths (-inf, 0].
       - Raw Anomaly Score: raw_score = -model.score_samples(X). Higher raw_score indicates higher anomaly severity.
    2. Score Normalization:
       - Raw scores are Min-Max scaled using fitted bounds (min_raw_score, max_raw_score):
         norm_score = clip((raw_score - min_raw) / (max_raw - min_raw), 0.0, 1.0)
    3. Threshold Calculation:
       - The anomaly threshold (threshold_norm) is derived deterministically at fit-time:
         threshold_norm = quantile(norm_scores, 1.0 - contamination)
    4. Anomaly Classification:
       - Event is anomalous if norm_score >= threshold_norm OR model.predict(X) == -1.
    """
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
        self.min_raw_score = 0.0
        self.max_raw_score = 1.0
        self.threshold_norm = 0.50
        self.is_fitted = False

    @property
    def threshold(self) -> float:
        return float(self.threshold_norm)

    @threshold.setter
    def threshold(self, val: float):
        self.threshold_norm = float(val)

    def fit(self, X: np.ndarray) -> "AnomalyDetector":
        self.model.fit(X)
        raw_scores = -self.model.score_samples(X)
        
        if len(raw_scores) > 0:
            self.min_raw_score = float(np.min(raw_scores))
            self.max_raw_score = float(np.max(raw_scores))
            denom = (self.max_raw_score - self.min_raw_score) if (self.max_raw_score - self.min_raw_score) > 1e-6 else 1.0
            norm_scores = (raw_scores - self.min_raw_score) / denom
            
            # Deterministic threshold based on contamination quantile (e.g. 1.0 - 0.33 = 0.67 quantile)
            computed_thresh = float(np.quantile(norm_scores, 1.0 - self.contamination))
            self.threshold_norm = max(0.40, min(0.95, computed_thresh))
        else:
            self.min_raw_score = 0.0
            self.max_raw_score = 1.0
            self.threshold_norm = 0.50

        self.is_fitted = True
        return self

    def predict_scores(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("AnomalyDetector must be fitted before calling predict_scores.")
        
        raw_scores = -self.model.score_samples(X)
        denom = (self.max_raw_score - self.min_raw_score) if (self.max_raw_score - self.min_raw_score) > 1e-6 else 1.0
        norm_scores = (raw_scores - self.min_raw_score) / denom
        return np.clip(norm_scores, 0.0, 1.0)

    def predict_anomalies(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if not self.is_fitted:
            raise RuntimeError("AnomalyDetector must be fitted before calling predict_anomalies.")

        norm_scores = self.predict_scores(X)
        iso_preds = self.model.predict(X)  # -1 for anomaly, +1 for inlier
        
        # Unified threshold strategy: Anomaly if norm_score >= threshold_norm OR IsolationForest predicts -1
        anomalies = (norm_scores >= self.threshold_norm) | (iso_preds == -1)
        return norm_scores, anomalies
