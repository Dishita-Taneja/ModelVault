# API Documentation
## PayGuard REST API — v1

**Base URL:** `https://api.payguard.dev/v1` (local: `http://localhost:4000/v1`)

---

## 1. Conventions

- All request/response bodies are JSON.
- All monetary amounts are integers in the smallest currency unit (e.g. paise for INR).
- Timestamps are ISO 8601 UTC.
- Authentication: `Authorization: Bearer <api_key_secret>` for server-to-server calls, or a JWT for dashboard-authenticated calls (see `07_Authentication.md`).
- Write endpoints (`POST`) require an `Idempotency-Key` header.

### Standard error format
```json
{
  "error": {
    "code": "idempotency_key_conflict",
    "message": "This Idempotency-Key was already used with a different request body.",
    "request_id": "req_9f2a1c"
  }
}
```

### Common error codes
| HTTP | code | Meaning |
|---|---|---|
| 400 | `validation_error` | Malformed request body |
| 401 | `unauthorized` | Missing/invalid API key or JWT |
| 403 | `forbidden` | Authenticated but not permitted |
| 404 | `not_found` | Resource doesn't exist |
| 409 | `conflict` | e.g. duplicate email on signup |
| 422 | `idempotency_key_conflict` | Same key, different payload |
| 429 | `rate_limited` | Too many requests — see `Retry-After` header |
| 500 | `internal_error` | Unexpected server error |

### Rate limit headers (present on every response)
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1755184800
```

### Pagination (list endpoints)
Cursor-based: `GET /v1/payments?limit=20&starting_after=pay_abc123`
Response includes `has_more: boolean` and `data: [...]`.

---

## 2. Auth Endpoints (dashboard)

### `POST /v1/auth/signup`
```json
// Request
{ "business_name": "Acme Co", "email": "founder@acme.com", "password": "•••••" }

// 201 Response
{ "merchant_id": "mer_1a2b3c", "user_id": "usr_9f8e7d" }
```

### `POST /v1/auth/login`
```json
// Request
{ "email": "founder@acme.com", "password": "•••••" }

// 200 Response
{ "access_token": "eyJhbGciOi...", "refresh_token": "eyJhbGciOi...", "expires_in": 900 }
```

### `POST /v1/auth/refresh`
```json
{ "refresh_token": "eyJhbGciOi..." }
```

---

## 3. API Keys

### `POST /v1/api-keys`  *(JWT auth)*
```json
// Request
{ "mode": "test" }

// 201 Response — secret shown ONCE
{
  "key_id": "pk_test_4f2a9b",
  "key_secret": "sk_test_7h3n2k9f1a...",
  "mode": "test",
  "created_at": "2026-08-14T10:00:00Z"
}
```

### `GET /v1/api-keys`  *(JWT auth)*
Returns list with `key_secret` omitted (only `key_id`, masked).

### `DELETE /v1/api-keys/{key_id}`  *(JWT auth)*
Revokes the key. `204 No Content`.

---

## 4. Payments  *(API key auth)*

### `POST /v1/payments`
Headers: `Authorization: Bearer sk_test_...`, `Idempotency-Key: <uuid>`

```json
// Request
{
  "amount": 150000,
  "currency": "INR",
  "customer": { "email": "buyer@example.com" },
  "payment_method": { "type": "mock_card", "card_number": "4242424242424242", "exp": "12/28" }
}

// 201 Response
{
  "id": "pay_9k2m1x",
  "status": "authorized",
  "amount": 150000,
  "currency": "INR",
  "fraud": { "status": "pending_review", "risk_score": null },
  "created_at": "2026-08-14T10:05:00Z"
}
```

If synchronous rules reject outright:
```json
// 200 Response, status reflects rejection — not an HTTP error, this is a valid business outcome
{ "id": "pay_9k2m1x", "status": "failed", "failure_reason": "sync_rule_blocked" }
```

### `GET /v1/payments/{id}`
Returns full payment object including `fraud_score` block once async scoring completes.

### `GET /v1/payments`
List with filters: `?status=flagged&created_after=2026-08-01&limit=20`

### `POST /v1/payments/{id}/capture`
Valid only from `authorized`. Idempotent.

### `POST /v1/refunds`
```json
{ "payment_id": "pay_9k2m1x", "amount": 50000 }
```

---

## 5. Fraud (internal / dashboard use)

### `GET /v1/payments/{id}/fraud-score`
```json
{
  "risk_score": 0.85,
  "model_version": "xgb-v3",
  "top_factors": ["high_velocity_last_hour", "new_device", "amount_outlier_for_customer"],
  "decision": "flagged"
}
```

### `POST /v1/payments/{id}/fraud-review`  *(JWT auth, `platform_admin` role)*
```json
{ "decision": "approve" }   // or "block"
```

---

## 6. Webhooks

### `POST /v1/webhooks`  *(JWT auth)*
```json
{
  "url": "https://merchant.example.com/webhooks/payguard",
  "event_types": ["payment.captured", "payment.flagged", "refund.created"]
}
// Response includes the signing secret once
```

### `GET /v1/webhooks/{id}/deliveries`
List of delivery attempts with status codes and retry state.

### `POST /v1/webhooks/deliveries/{id}/replay`
Manually re-triggers a dead-lettered delivery.

**Webhook payload delivered to merchant's URL:**
```json
{
  "event": "payment.flagged",
  "payment_id": "pay_9k2m1x",
  "data": { "status": "flagged", "risk_score": 0.85 },
  "sent_at": "2026-08-14T10:05:03Z"
}
```
Header `X-PayGuard-Signature: sha256=<hmac>` — merchant verifies against their webhook secret.

---

## 7. Analytics (dashboard)

### `GET /v1/analytics/summary?range=30d`
```json
{
  "total_volume": 45200000,
  "transaction_count": 312,
  "approval_rate": 0.94,
  "fraud_rate": 0.021
}
```
