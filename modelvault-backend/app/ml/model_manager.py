import datetime
from pathlib import Path
from typing import Any

import joblib

from app.core.logging import logger
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.feature_engineering import FeatureEngineeringPipeline

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
DEFAULT_MODEL_PATH = ARTIFACTS_DIR / "model_latest.joblib"


class ModelManager:
    def __init__(self, artifacts_dir: Path | None = None):
        self.artifacts_dir = Path(artifacts_dir) if artifacts_dir else ARTIFACTS_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        detector: AnomalyDetector,
        pipeline: FeatureEngineeringPipeline,
        model_version: str = "v1.0.0",
        training_stats: dict[str, Any] | None = None,
        file_path: Path | None = None
    ) -> Path:
        save_path = file_path if file_path else self.artifacts_dir / f"model_{model_version}.joblib"
        latest_path = self.artifacts_dir / "model_latest.joblib"

        artifact = {
            "detector": detector,
            "pipeline": pipeline,
            "feature_names": pipeline.feature_names,
            "model_version": model_version,
            "training_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "threshold": detector.threshold,
            "configuration": {
                "contamination": detector.contamination,
                "n_estimators": detector.n_estimators,
                "random_state": detector.random_state
            },
            "training_stats": training_stats or {}
        }

        joblib.dump(artifact, save_path)
        joblib.dump(artifact, latest_path)
        logger.info(f"Model artifact persisted successfully to {save_path} and {latest_path}")
        return save_path

    def load_model(self, file_path: Path | None = None) -> tuple[AnomalyDetector, FeatureEngineeringPipeline, dict[str, Any]]:
        target_path = file_path if file_path else self.artifacts_dir / "model_latest.joblib"
        if not target_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {target_path}. Run training pipeline first.")

        artifact = joblib.load(target_path)
        logger.info(f"Loaded model artifact version {artifact.get('model_version')} from {target_path}")
        return artifact["detector"], artifact["pipeline"], artifact


model_manager = ModelManager()
