import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.preprocessing import StandardScaler
from dateutil import parser

FEATURE_NAMES = [
    "bytes_transferred_log",
    "is_large_transfer",
    "is_model_weight_access",
    "hour_of_day",
    "day_of_week",
    "is_off_hours",
    "model_sensitivity_score",
    "user_access_frequency",
    "is_privileged_action",
    "cross_source_count"
]

PRIVILEGED_ACTIONS = {"CreateAccessKey", "AssumeRole", "RunInstances", "AttachUserPolicy"}


class FeatureEngineeringPipeline:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = FEATURE_NAMES
        self.is_fitted = False

    def extract_features(
        self,
        events: List[Dict[str, Any]],
        models_metadata: Optional[List[Dict[str, Any]]] = None,
        users_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> pd.DataFrame:
        if not events:
            return pd.DataFrame(columns=self.feature_names)

        df = pd.DataFrame(events)

        # Ensure required keys exist
        if "bytes_transferred" not in df.columns:
            df["bytes_transferred"] = 0
        df["bytes_transferred"] = df["bytes_transferred"].fillna(0).astype(float)

        if "source" not in df.columns and "log_source" in df.columns:
            df["source"] = df["log_source"]
        if "source" not in df.columns:
            df["source"] = "UNKNOWN"

        if "event_name" not in df.columns and "action" in df.columns:
            df["event_name"] = df["action"]
        if "event_name" not in df.columns:
            df["event_name"] = "UNKNOWN"

        # Model sensitivity map
        model_sens_map = {}
        if models_metadata:
            for m in models_metadata:
                model_id = m.get("model_id")
                sens = m.get("sensitivity_level", "HIGH")
                score = {"CRITICAL": 3.0, "HIGH": 2.0, "MEDIUM": 1.0}.get(sens, 0.0)
                if model_id:
                    model_sens_map[model_id] = score

        # Build feature columns
        df["bytes_transferred_log"] = np.log1p(df["bytes_transferred"])
        df["is_large_transfer"] = (df["bytes_transferred"] >= 1e9).astype(float)

        # Model weight access indicator
        def check_weight_access(row):
            src = str(row.get("source", "")).upper()
            extra = row.get("extra", {}) if isinstance(row.get("extra"), dict) else {}
            key = str(extra.get("key", ""))
            resource = str(row.get("resource_arn", ""))
            if src == "MODEL":
                return 1.0
            if src == "S3" and any(ext in key or ext in resource for ext in [".bin", ".safetensors", ".pt", ".onnx", "model"]):
                return 1.0
            return 0.0

        df["is_model_weight_access"] = df.apply(check_weight_access, axis=1)

        # Time features
        def get_dt(row):
            ts = row.get("event_time_raw") or row.get("timestamp")
            if isinstance(ts, str):
                return parser.parse(ts)
            return ts

        timestamps = df.apply(get_dt, axis=1)
        df["hour_of_day"] = timestamps.apply(lambda dt: dt.hour if dt else 12)
        df["day_of_week"] = timestamps.apply(lambda dt: dt.weekday() if dt else 0)
        df["is_off_hours"] = ((df["hour_of_day"] < 8) | (df["hour_of_day"] >= 18)).astype(float)

        # Model sensitivity
        def get_model_sens(row):
            mid = row.get("model_id")
            if mid in model_sens_map:
                return model_sens_map[mid]
            if mid:
                return 2.0  # default high sensitivity
            return 0.0

        df["model_sensitivity_score"] = df.apply(get_model_sens, axis=1)

        # User access frequency
        user_col = "user_id" if "user_id" in df.columns else "user_name"
        user_counts = df[user_col].value_counts().to_dict()
        df["user_access_frequency"] = df[user_col].map(user_counts).fillna(1.0).astype(float)

        # Privileged action indicator
        df["is_privileged_action"] = df["event_name"].apply(
            lambda act: 1.0 if str(act) in PRIVILEGED_ACTIONS else 0.0
        )

        # Cross-source count
        ip_col = "ip_address" if "ip_address" in df.columns else "source_ip"
        ip_counts = df[ip_col].value_counts().to_dict()
        df["cross_source_count"] = df[ip_col].map(ip_counts).fillna(1.0).astype(float)

        return df[self.feature_names]

    def fit_transform(
        self,
        events: List[Dict[str, Any]],
        models_metadata: Optional[List[Dict[str, Any]]] = None,
        users_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        X_df = self.extract_features(events, models_metadata, users_metadata)
        X_scaled = self.scaler.fit_transform(X_df)
        self.is_fitted = True
        return X_scaled

    def transform(
        self,
        events: List[Dict[str, Any]],
        models_metadata: Optional[List[Dict[str, Any]]] = None,
        users_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        X_df = self.extract_features(events, models_metadata, users_metadata)
        if not self.is_fitted:
            return self.scaler.fit_transform(X_df)
        return self.scaler.transform(X_df)
