# Feature Specification
## PayGuard

Priority key: **P0** = must have to demo, **P1** = should have, **P2** = nice to have / stretch.

---

## F1. Merchant Signup & Login (P0)
**User story:** As a business owner, I can create an account and log into a dashboard.

**Acceptance criteria:**
- Signup requires email, password, business name → creates `merchant` + `merchant_user` records
- Passwords hashed with bcrypt/argon2, never stored/logged in plaintext
- Login returns a short-lived JWT access token + refresh token
- Duplicate email signup returns `409 Conflict`, not a generic 500

---

## F2. API Key Management (P0)
**User story:** As a merchant, I can generate API keys to call the payment API from my own server.

**Acceptance criteria:**
- Dashboard action generates a key pair: `key_id` (visible) + `key_secret` (shown once, then only a hash is stored)
- Support "test mode" and "live mode" keys (prefix `pk_test_` / `pk_live_`) — mirrors how Razorpay/Stripe do it, good talking point
- Keys can be revoked; revoked keys fail auth immediately
- At least one key required before any `/payments` call succeeds

---

## F3. Create Payment (P0)
**User story:** As a merchant's backend, I can create a payment for a customer.

**Acceptance criteria:**
- `POST /v1/payments` with amount, currency, customer info, payment method (mock card)
- Requires `Idempotency-Key` header (see F4)
- Runs synchronous fraud pre-check (fast rules) before authorizing (see F6)
- Returns a payment object with status: `created → authorized → captured` or `failed` / `flagged`
- Amount stored in smallest currency unit (paise/cents) as an integer — **never a float**

---

## F4. Idempotent Requests (P0)
**User story:** As a merchant's backend, if my request times out and I retry it, I must not double-charge the customer.

**Acceptance criteria:**
- Every write endpoint (`POST`) requires `Idempotency-Key` header
- Same key + same merchant + same request body within a TTL window (e.g. 24h) → returns the original response, does not re-execute
- Same key with a *different* request body → `422` conflict error (this is the case people forget)
- Idempotency keys stored in Redis (fast lookup) with the response payload cached

---

## F5. Capture & Refund (P1)
**User story:** As a merchant, I can capture an authorized payment and issue full/partial refunds.

**Acceptance criteria:**
- `POST /v1/payments/{id}/capture` only valid from `authorized` state
- `POST /v1/refunds` supports partial refunds; total refunded amount cannot exceed captured amount
- Both actions emit webhook events and are idempotent

---

## F6. Real-Time Fraud Scoring (P0)
**User story:** As the platform, every payment is scored for fraud risk before it completes.

**Acceptance criteria:**
- Two-tier scoring:
  - **Synchronous rules layer** (velocity checks, amount thresholds, blocklisted BIN/email) — runs inline, adds minimal latency
  - **Async ML layer** — a trained classifier scores the transaction after authorization; if score exceeds threshold, payment status flips to `flagged` and a webhook fires
- Every scored transaction stores its risk score (0–1) and contributing factors, visible in the dashboard
- Flagged transactions are held (not auto-captured) pending admin review

---

## F7. Fraud Review Workflow (P1)
**User story:** As a risk analyst, I can see flagged transactions and approve or block them.

**Acceptance criteria:**
- Admin dashboard lists flagged transactions sorted by risk score
- Approve → payment proceeds to `captured`; Block → payment moves to `failed`, customer/merchant notified via webhook
- Every decision is audit-logged with analyst ID + timestamp

---

## F8. Webhook Notification System (P0)
**User story:** As a merchant, my server gets notified when payment status changes, without polling.

**Acceptance criteria:**
- Merchant registers a webhook URL + selects event types (`payment.authorized`, `payment.captured`, `payment.flagged`, `payment.failed`, `refund.created`)
- Payload signed with HMAC-SHA256 using the merchant's webhook secret; header `X-PayGuard-Signature`
- Delivery retried with exponential backoff (e.g. 1m, 5m, 30m, 2h, 12h) up to 5 attempts
- After max attempts, delivery marked `dead_letter` and visible in dashboard for manual replay

---

## F9. Rate Limiting (P1)
**User story:** As the platform, I protect against abuse and runaway retries.

**Acceptance criteria:**
- Per-API-key sliding window limit (e.g. 100 req/min), enforced via Redis
- `429` response includes `Retry-After` header
- Limits configurable per merchant tier (even if only one tier exists in V1, design for it)

---

## F10. Merchant Dashboard (P1)
**User story:** As a merchant, I can see my transaction history, fraud alerts, and basic analytics without calling the API.

**Acceptance criteria:**
- Transactions list with filter/search (status, date range, amount)
- Transaction detail view showing full event timeline + fraud score breakdown
- Simple analytics: volume over time, approval rate, fraud rate
- API key & webhook management screens (from F2, F8)

---

## F11. Authentication & Authorization (P0)
See `07_Authentication.md` for full detail.

**Acceptance criteria:**
- Two distinct auth mechanisms: API key (server-to-server) and JWT (dashboard sessions)
- Role-based access: `merchant_admin`, `merchant_staff`, `platform_admin`
- All endpoints reject unauthenticated/unauthorized requests with correct 401/403 (not 500)

---

## F12. Audit Logging (P2)
**User story:** As the platform, every sensitive action is traceable.

**Acceptance criteria:**
- Login, key generation/revocation, fraud review decisions, refunds all write an `audit_log` row
- Logs are append-only from the application's perspective (no update/delete endpoint)
