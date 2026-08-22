/**
 * ModelVault Mock Threat Intelligence Data
 * Matches the exact backend payload contract for seamless drop-in API replacement.
 */

export const mockData = {
  stats: {
    total_models: 42,
    flagged_count: 7,
    active_anomalies: 9,
  },
  topSuspicious: [
    {
      model_id: "mod-c87a1e94-9b2f-410a-b0fa-d205167b001a",
      model_name: "internal-enterprise-llm-weights",
      owner: "bob.martinez",
      anomaly_score: 0.98,
      reason: "Massive unauthorized model weight download (14.5GB) via direct S3 API from untrusted proxy IP outside business hours.",
      flagged_at: "2026-08-22T03:14:22Z",
      reviewed: false,
      evidence: [
        {
          event_id: "evt-09f4e21a-412d-419b-810a-011293a001",
          source: "S3",
          event_name: "GetObject (Weights Archive)",
          event_time_reconciled: "2026-08-22T03:12:45Z",
          ip_address: "198.51.100.42",
          extra: {
            bucket: "s3://modelvault-weights-prod/checkpoints/llm-v4-full.bin",
            bytes_transferred: 15569256448,
            user_agent: "aws-sdk-go/v1.44.0 (custom-cli)",
            geo_region: "Unknown/Commercial Proxy",
            asn: "AS13335 (Cloudflare)",
            session_duration_s: 412,
            mfa_authenticated: false
          }
        },
        {
          event_id: "evt-09f4e21a-412d-419b-810a-011293a002",
          source: "IAM",
          event_name: "AssumeRoleWithWebIdentity",
          event_time_reconciled: "2026-08-22T03:10:02Z",
          ip_address: "198.51.100.42",
          extra: {
            assumed_role_arn: "arn:aws:iam::882190412891:role/ModelSyncPipeline",
            token_issuer: "stolen-service-token-eval",
            risk_indicator: "Token geographic anomaly (+8,400 miles from registered identity)"
          }
        },
        {
          event_id: "evt-09f4e21a-412d-419b-810a-011293a003",
          source: "API_GATEWAY",
          event_name: "TokenValidationBypass",
          event_time_reconciled: "2026-08-22T03:09:18Z",
          ip_address: "198.51.100.42",
          extra: {
            http_status: 401,
            retry_count: 14,
            payload_signature: "mismatched-hmac-sha256"
          }
        }
      ]
    },
    {
      model_id: "mod-a11b93f2-140e-4328-89c2-77182239401f",
      model_name: "fraud-detection-transformer-v3",
      owner: "alice.chen",
      anomaly_score: 0.91,
      reason: "Unauthorized elevation of privilege assuming EmergencyAccess role to export critical fraud detection model weights.",
      flagged_at: "2026-08-22T04:44:10Z",
      reviewed: false,
      evidence: [
        {
          event_id: "evt-81bb204c-6231-482a-9241-1188339401",
          source: "IAM",
          event_name: "AssumeRole (EmergencyAccess)",
          event_time_reconciled: "2026-08-22T04:42:01Z",
          ip_address: "203.0.113.19",
          extra: {
            principal: "arn:aws:iam::882190412891:user/contractor_temp_eve",
            target_role: "arn:aws:iam::882190412891:role/SecOpsEmergencyAccess",
            policy_overridden: true,
            justification_note: "Ad-hoc debugging latency spike in production"
          }
        },
        {
          event_id: "evt-81bb204c-6231-482a-9241-1188339402",
          source: "EC2",
          event_name: "DirectArtifactExport",
          event_time_reconciled: "2026-08-22T04:43:18Z",
          ip_address: "10.0.94.120",
          extra: {
            source_cluster: "prod-us-east-inference-04",
            destination_endpoint: "external-backup-sync.storage.io",
            bytes_transferred: 3829104800,
            tls_version: "TLSv1.3",
            encryption_cipher: "ChaCha20-Poly1305"
          }
        }
      ]
    },
    {
      model_id: "mod-f448201a-7b33-4f91-872e-09941198302b",
      model_name: "credit-risk-scoring-v2",
      owner: "alice.chen",
      anomaly_score: 0.84,
      reason: "Extreme query rate anomaly (450 req/sec) consistent with model extraction / model inversion adversarial attack.",
      flagged_at: "2026-08-22T06:10:05Z",
      reviewed: true,
      evidence: [
        {
          event_id: "evt-55aa91bc-3341-4701-a128-4491028301",
          source: "API_GATEWAY",
          event_name: "InferenceBatchSpike",
          event_time_reconciled: "2026-08-22T06:08:30Z",
          ip_address: "198.51.100.42",
          extra: {
            requests_per_second: 450,
            baseline_normal_rps: 12.4,
            token_count_total: 1240000,
            deviations_from_mean_sigma: 5.8,
            payload_entropy: "0.994 (High entropy synthetic vectors)"
          }
        },
        {
          event_id: "evt-55aa91bc-3341-4701-a128-4491028302",
          source: "KUBERNETES",
          event_name: "PodAutoscaleTrigger",
          event_time_reconciled: "2026-08-22T06:09:12Z",
          ip_address: "10.244.18.4",
          extra: {
            deployment: "credit-risk-serving-deploy",
            replica_count_initial: 3,
            replica_count_scaled: 18,
            cpu_utilization_pct: 98.6
          }
        }
      ]
    }
  ],
  flaggedModels: [
    {
      model_id: "mod-c87a1e94-9b2f-410a-b0fa-d205167b001a",
      model_name: "internal-enterprise-llm-weights",
      owner: "bob.martinez",
      anomaly_score: 0.98,
      reason: "Massive unauthorized model weight download (14.5GB) via direct S3 API from untrusted proxy IP outside business hours.",
      flagged_at: "2026-08-22T03:14:22Z",
      reviewed: false,
      evidence: [
        {
          event_id: "evt-09f4e21a-412d-419b-810a-011293a001",
          source: "S3",
          event_name: "GetObject (Weights Archive)",
          event_time_reconciled: "2026-08-22T03:12:45Z",
          ip_address: "198.51.100.42",
          extra: {
            bucket: "s3://modelvault-weights-prod/checkpoints/llm-v4-full.bin",
            bytes_transferred: 15569256448,
            user_agent: "aws-sdk-go/v1.44.0 (custom-cli)",
            geo_region: "Unknown/Commercial Proxy"
          }
        },
        {
          event_id: "evt-09f4e21a-412d-419b-810a-011293a002",
          source: "IAM",
          event_name: "AssumeRoleWithWebIdentity",
          event_time_reconciled: "2026-08-22T03:10:02Z",
          ip_address: "198.51.100.42",
          extra: {
            assumed_role_arn: "arn:aws:iam::882190412891:role/ModelSyncPipeline",
            risk_indicator: "Token geographic anomaly"
          }
        }
      ]
    },
    {
      model_id: "mod-a11b93f2-140e-4328-89c2-77182239401f",
      model_name: "fraud-detection-transformer-v3",
      owner: "alice.chen",
      anomaly_score: 0.91,
      reason: "Unauthorized elevation of privilege assuming EmergencyAccess role to export critical fraud detection model weights.",
      flagged_at: "2026-08-22T04:44:10Z",
      reviewed: false,
      evidence: [
        {
          event_id: "evt-81bb204c-6231-482a-9241-1188339401",
          source: "IAM",
          event_name: "AssumeRole (EmergencyAccess)",
          event_time_reconciled: "2026-08-22T04:42:01Z",
          ip_address: "203.0.113.19",
          extra: {
            principal: "contractor_temp_eve",
            policy_overridden: true
          }
        },
        {
          event_id: "evt-81bb204c-6231-482a-9241-1188339402",
          source: "EC2",
          event_name: "DirectArtifactExport",
          event_time_reconciled: "2026-08-22T04:43:18Z",
          ip_address: "10.0.94.120",
          extra: {
            destination_endpoint: "external-backup-sync.storage.io",
            bytes_transferred: 3829104800
          }
        }
      ]
    },
    {
      model_id: "mod-f448201a-7b33-4f91-872e-09941198302b",
      model_name: "credit-risk-scoring-v2",
      owner: "alice.chen",
      anomaly_score: 0.84,
      reason: "Extreme query rate anomaly (450 req/sec) consistent with model extraction / model inversion adversarial attack.",
      flagged_at: "2026-08-22T06:10:05Z",
      reviewed: true,
      evidence: [
        {
          event_id: "evt-55aa91bc-3341-4701-a128-4491028301",
          source: "API_GATEWAY",
          event_name: "InferenceBatchSpike",
          event_time_reconciled: "2026-08-22T06:08:30Z",
          ip_address: "198.51.100.42",
          extra: {
            requests_per_second: 450,
            token_count_total: 1240000
          }
        }
      ]
    },
    {
      model_id: "mod-33b81109-88ae-4102-a1f9-55091277401c",
      model_name: "biometric-face-encoder-v5",
      owner: "david.kim",
      anomaly_score: 0.76,
      reason: "Atypical embedding inference pipeline triggered from non-whitelisted VPC peering subnet.",
      flagged_at: "2026-08-22T07:22:15Z",
      reviewed: false,
      evidence: [
        {
          event_id: "evt-124985aa-9901-41fb-9923-8827401928",
          source: "EC2",
          event_name: "CrossVPCInferenceRequest",
          event_time_reconciled: "2026-08-22T07:21:40Z",
          ip_address: "172.31.84.212",
          extra: {
            vpc_id: "vpc-0899120938f",
            peering_connection: "pcx-012ab99f8",
            unauthorized_subnet: "subnet-09f1823ab"
          }
        }
      ]
    },
    {
      model_id: "mod-909281a7-009e-4f22-bd88-12903849104d",
      model_name: "sentinel-guard-embeddings",
      owner: "sarah.connor",
      anomaly_score: 0.58,
      reason: "Moderate query volume deviation and burst token concurrency exceeding standard baseline by 2.4x.",
      flagged_at: "2026-08-22T08:05:40Z",
      reviewed: true,
      evidence: [
        {
          event_id: "evt-776102aa-bb19-4921-9988-1029384819",
          source: "API_GATEWAY",
          event_name: "ConcurrencyThresholdExceeded",
          event_time_reconciled: "2026-08-22T08:04:12Z",
          ip_address: "192.0.2.145",
          extra: {
            concurrent_streams: 64,
            quota_limit: 25,
            api_key_prefix: "sk_live_sentinel_09"
          }
        }
      ]
    },
    {
      model_id: "mod-66120938-f99a-4122-8811-00293847119e",
      model_name: "customer-churn-xgb",
      owner: "bob.martinez",
      anomaly_score: 0.42,
      reason: "Off-hours parameter exploration query sequence detected during scheduled staging maintenance window.",
      flagged_at: "2026-08-22T09:18:30Z",
      reviewed: true,
      evidence: [
        {
          event_id: "evt-90182736-4411-4a92-8822-0918273645",
          source: "KUBERNETES",
          event_name: "CronJobEvaluationRun",
          event_time_reconciled: "2026-08-22T09:17:00Z",
          ip_address: "10.244.3.18",
          extra: {
            cluster: "staging-us-west-2",
            namespace: "analytics-batch",
            job_name: "churn-eval-offcycle"
          }
        }
      ]
    },
    {
      model_id: "mod-11928374-bb22-4a00-9911-38291049582f",
      model_name: "speech-transcription-whisper-finetuned",
      owner: "elena.rostova",
      anomaly_score: 0.22,
      reason: "Minor latency jitter and temporary cache miss cascade under normal production load.",
      flagged_at: "2026-08-22T10:45:00Z",
      reviewed: true,
      evidence: [
        {
          event_id: "evt-33991122-0011-44bb-8822-1928374650",
          source: "API_GATEWAY",
          event_name: "CacheMissFallback",
          event_time_reconciled: "2026-08-22T10:44:15Z",
          ip_address: "198.51.100.8",
          extra: {
            cache_hit_rate_pct: 74.2,
            p99_latency_ms: 182,
            status_code: 200
          }
        }
      ]
    }
  ]
};
