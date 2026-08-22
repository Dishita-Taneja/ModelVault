# Authentication & Authorization Document
## PayGuard

Two independent auth mechanisms, for two independent audiences. Keep them fully separate in code — don't let one middleware try to handle both.

---

## 1. API Key Auth (merchant server → PayGuard API)

Used for all `/v1/payments`, `/v1/refunds` calls — i.e. anything a merchant's backend calls directly.

### Key structure
- `key_id`: public identifier, safe to log, format `pk_{mode}_{random}` e.g. `pk_test_4f2a9b`
- `key_secret`: sensitive, format `sk_{mode}_{random}`, shown to the merchant **exactly once** at generation time

### Storage
- Store only `SHA-256(key_secret)` in the database, never the plaintext secret.
- `key_id` is indexed for fast lookup; on request, hash the presented secret and compare against the stored hash (constant-time comparison to avoid timing attacks).

### Request flow
```
Authorization: Bearer sk_test_7h3n2k9f1a...
```
1. Middleware extracts the bearer token.
2. Looks up by prefix/`key_id` embedded convention or by hashing and matching — simplest: require both `key_id` and secret, or derive `key_id` from the first N chars of the secret at generation time and store the mapping.
3. Checks `status = active`; rejects `revoked` keys with `401`.
4. Attaches `merchant_id` and `mode` (test/live) to the request context for downstream handlers.
5. Updates `last_used_at` (async, don't block the request on this write).

### Test vs live mode
- Test-mode keys only operate on test-mode data (payments created with a test key are tagged `mode=test` and excluded from live analytics). This mirrors Stripe/Razorpay and is worth doing — it's a real product decision, not busywork.

### Optional stretch: request signing (HMAC)
For a stronger security story, require merchants to sign requests:
```
X-PayGuard-Signature: sha256=HMAC(key_secret, timestamp + "." + raw_body)
X-PayGuard-Timestamp: 1755184800
```
Reject requests where the timestamp is more than 5 minutes old (replay protection). This is optional but is a strong thing to mention in an interview even if you only implement it for one endpoint as a demonstration.

---

## 2. JWT Auth (dashboard sessions)

Used for the merchant/admin dashboard — humans logging in via browser.

### Login flow
1. `POST /v1/auth/login` with email + password.
2. Password checked against `bcrypt`/`argon2` hash — never plaintext comparison.
3. On success, issue:
   - **Access token** (JWT, short-lived — 15 min), contains `sub` (user id), `merchant_id`, `role`, `exp`
   - **Refresh token** (opaque random string or JWT, long-lived — 7–30 days), stored server-side (hashed) so it can be revoked
4. Access token sent as `Authorization: Bearer <jwt>` on subsequent dashboard API calls.
5. Refresh token used at `/v1/auth/refresh` to mint a new access token when the old one expires — client should do this transparently.

### Token rotation
- On refresh, issue a **new** refresh token and invalidate the old one (rotation). If an old, already-rotated refresh token is presented, treat it as a signal of possible theft and revoke the entire token family.

### Roles
| Role | Scope |
|---|---|
| `merchant_admin` | Full access to their merchant's data: keys, webhooks, transactions, team management |
| `merchant_staff` | Read-only + fraud review, no key/webhook management |
| `platform_admin` | Cross-merchant access, fraud review across all merchants (this is *your* internal role for the demo — represents PayGuard's own risk team) |

### Authorization middleware pattern
```
authenticate(jwt) → attaches { userId, merchantId, role } to req
authorize(requiredRole) → checks req.role against an allowlist for the route
```
Keep these as two composable middlewares, not one big function — makes it trivial to explain and trivial to unit test.

---

## 3. Security Practices Worth Implementing (and mentioning)

- **HTTPS only** in any deployed environment; reject/redirect plain HTTP.
- **Rate limit auth endpoints separately** and more strictly than general API traffic (`/auth/login` especially — brute-force target).
- **Account lockout / backoff** after N failed login attempts.
- **Never log** API key secrets, JWTs, or raw card data — scrub these in your logging middleware explicitly. This is a small thing to implement but a strong thing to say out loud in an interview.
- **CORS** locked to the known dashboard origin(s) in production.
- **Secrets management:** DB credentials, JWT signing key, HMAC secrets all come from environment variables / a secrets manager — never hardcoded, never committed.
- **Audit every sensitive action** (key generation/revocation, fraud decisions, login) — see `audit_logs` table in the Database Design doc.

---

## 4. What NOT to build (scope guard)

- No real card storage — mock card data only, and treat it with the same discipline as if it were real (this "as if it were real" framing is itself worth stating explicitly when you present the project).
- No OAuth/social login needed for V1 — email/password is enough; don't burn time here.
- No 2FA required for V1, but note it as a documented "next step" in your README — shows you know what's missing without overbuilding.
