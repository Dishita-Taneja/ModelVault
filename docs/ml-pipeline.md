# ModelVault - Unsupervised ML Anomaly Detection Pipeline

**Document**: `docs/ml-pipeline.md`  
**Service**: ModelVault ML Core (`app/ml/`)  
**Primary Algorithm**: `scikit-learn` `IsolationForest`  
**Purpose**: Technical documentation detailing behavioral feature engineering, model training, persistence, threshold selection, evaluation, and REST API architecture.

---

## 1. Feature Engineering & Preprocessing

Raw identifiers (`event_id`, `user_id`, `model_id`, `ip_address`) are **not** passed directly into the ML model. Instead, domain-specific security behavioral features are extracted:

| Feature Name | Source Field | Description | Formula / Transformation |
| :--- | :--- | :--- | :--- |
| `bytes_transferred_log` | `bytes_transferred` | Log-transformed byte volume | $\log(1 + \text{bytes\_transferred})$ |
| `is_large_transfer` | `bytes_transferred` | Exfiltration indicator | $1.0$ if $\ge 1\text{GB}$, else $0.0$ |
| `is_model_weight_access` | `log_source`, `key`, `resource_arn` | Model weight file access | $1.0$ if S3 key matches `.bin`, `.safetensors`, `.pt` or Model Endpoint, else $0.0$ |
| `hour_of_day` | `timestamp` | UTC hour of activity | $0 \dots 23$ |
| `day_of_week` | `timestamp` | Day of week | $0 \dots 6$ |
| `is_off_hours` | `hour_of_day` | Off-hours access indicator | $1.0$ if hour $< 8$ or $\ge 18$, else $0.0$ |
| `model_sensitivity_score` | `models.json` `sensitivity_level` | Sensitivity weighting | `CRITICAL`=$3.0$, `HIGH`=$2.0$, `MEDIUM`=$1.0$, default=$0.0$ |
| `user_access_frequency` | `user_id` / `user_name` | Frequency of events per user | Count of user occurrences in dataset |
| `is_privileged_action` | `action` | Sensitive IAM/Compute action | $1.0$ if in (`CreateAccessKey`, `AssumeRole`, `RunInstances`), else $0.0$ |
| `cross_source_count` | `source_ip` / `user_name` | Multi-source activity volume | Count of correlated events per IP/User |

### Preprocessing
Features are scaled using `StandardScaler` (`app/ml/feature_engineering.py`). The fitted scaler is saved alongside the model artifact to ensure identical feature scaling during inference.

---

## 2. Isolation Forest Model & Training Pipeline

### Model Architecture
- **Algorithm**: `sklearn.ensemble.IsolationForest`
- **Hyperparameters**:
  - `n_estimators`: 100
  - `contamination`: 0.33 (Expected anomaly ratio in threat scenarios)
  - `random_state`: 42 (Ensures reproducible training)
- **Unsupervised Learning Constraint**: No explicit ground-truth labels (`anomaly_flag`, `risk_score`) are used during model training to avoid target leakage.

### Reproducible Training Workflow ([`app/ml/training.py`](file:///c:/Users/Admin/OneDrive/Desktop/ModelVault/backend/app/ml/training.py))
```
Raw Events / DB Persistence
   ├──> Feature Engineering & Scaling
   ├──> IsolationForest.fit(X_scaled)
   ├──> Decision Score & Threshold Calculation
   └──> Persist Model Artifact (joblib)
```

---

## 3. Threshold Selection & Anomaly Scoring

- Raw decision scores $s_{\text{raw}} = -\text{score\_samples}(X)$ are computed (where higher values represent greater isolation distance).
- Scores are Min-Max normalized to the $[0.0, 1.0]$ interval.
- **Threshold Criterion**: An event is flagged as anomalous (`is_anomaly = True`) if normalized score $\ge 0.65$ or raw score $\ge \tau_{90\%}$.

---

## 4. Evaluation & Performance

- **Performance Constraint**: Processes 1000+ records in $< 1000\text{ms}$, well within the PRD 5-minute requirement.
- **Traceability**: Each anomaly result persisted to `anomaly_results` table maintains trace links to `event_id`, `user_id`, `model_id`, and `feature_values`.

---

## 5. API Architecture

- **`POST /api/v1/ml/train`**: Triggers ML model training and persists artifact `.joblib`.
- **`POST /api/v1/ml/detect`**: Executes inference using active artifact and stores anomaly records in DB.
- **`GET /api/v1/ml/results`**: Lists persisted anomaly detection results.
- **`GET /api/v1/ml/results/top`**: Returns top N highest risk anomalous events (PRD Item 8).

---

## 6. Limitations & Future Work

1. **Cold-Start for New Users**: Users with single-event histories rely on global population behavioral baseline features until session history accumulates.
2. **Online Learning**: Current pipeline performs batch retrains; future phases can add real-time incremental scoring queues.
