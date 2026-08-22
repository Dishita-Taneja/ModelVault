# ModelVault - Deterministic Timestamp Reconciliation Engine

**Document**: `docs/timestamp-reconciliation.md`  
**Service**: ModelVault Backend  
**Purpose**: Technical documentation of the deterministic timestamp reconciliation algorithm used to correlate heterogeneous multi-source cloud logs (IAM, EC2, S3, Model Endpoint) and validate temporal alignment against reference evidence datasets (`data/normalized_events.csv`).

---

## 1. Overview & Data Context

In cloud security forensics, log events originate from disparate services with independent clock sources, network transit latencies, and logging formats:
- **IAM Logs (`iam_logs.json`)**: Identity actions (`ConsoleLogin`, `CreateAccessKey`, `AssumeRole`).
- **EC2 Logs (`ec2_logs.json`)**: Compute infrastructure actions (`DescribeInstances`, `RunInstances`).
- **S3 Logs (`s3_logs.json`)**: Storage access (`GetObject` model weights download).
- **Model Access Logs (`model_access_logs.json`)**: ML inference endpoint invocations (`InvokeEndpoint`).

The reference dataset `data/normalized_events.csv` establishes ground-truth evidence correlating these events into structured timelines.

---

## 2. Deterministic Reconciliation Algorithm

### Step 1: UTC Timestamp Normalization
All input raw timestamps are parsed and converted to ISO-8601 UTC standard datetimes (`event_time_raw` and `event_time_normalized`).

### Step 2: Multi-Source Session & Identity Clustering
Events are clustered into session chains based on matching correlation keys:
- Primary Key: `ip_address` (e.g. `198.51.100.42` for compromised session, `192.168.1.50` for analyst session).
- Secondary Key: `user_name` / `user_arn` (e.g. `arn:aws:iam::123456789012:user/charlie.compromised`).
- Tertiary Key: `model_id` (e.g. `mdl-llm-01`).

### Step 3: Causal Sequence Alignment
The reconciliation engine evaluates temporal ordering across cross-source event chains:
1. **Primary Anchor Alignment (`PRIMARY_SOURCE_ANCHOR`)**:
   - Used when event raw timestamp cleanly anchors the event without clock drift.
   - Confidence Score: `0.90`.
2. **Cross-Source Triangulation (`CROSS_SOURCE_TRIANGULATION`)**:
   - Triggered when an event is corroborated by multiple matching log sources within the same identity session (e.g. S3 model weight download + IAM credentials + Model endpoint invocation).
   - Confidence Score: `0.95` (2 sources) or `1.0` (3+ sources).
3. **Temporal Skew Correction (`TEMPORAL_SEQUENCE_ALIGNMENT`)**:
   - Adjusts timestamp offsets when log delivery skew is detected between causally linked operations.

---

## 3. Auditable Output Fields

For every reconciled event, the engine generates an auditable record (`ReconciliationResult`):

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `event_id` | String | Target normalized event ID |
| `event_time_raw` | DateTime | Original raw timestamp from log payload |
| `event_time_reconciled` | DateTime | Final reconciled UTC timestamp |
| `timestamp_offset_seconds` | Float | Difference in seconds (`event_time_reconciled - event_time_raw`) |
| `confidence_score` | Float | Statistical confidence (0.0 to 1.0) |
| `reconciliation_method` | String | Method (`PRIMARY_SOURCE_ANCHOR`, `CROSS_SOURCE_TRIANGULATION`) |
| `reason_for_change` | Text | Human-readable audit explanation |
| `source_events_used` | JSON Array | Array of correlated raw event IDs supporting reconciliation |

---

## 4. API Endpoints

- **`POST /api/v1/reconciliation/run`**: Executes reconciliation engine over all stored events and persists auditable results.
- **`GET /api/v1/reconciliation/`**: Retrieves summary list of all timestamp reconciliations.
- **`GET /api/v1/reconciliation/{event_id}`**: Retrieves complete audit details for a specific event ID.
