# Product Requirements Document (PRD)
## PayGuard — Payment Processing Platform with Real-Time Fraud Detection

**Version:** 1.0
**Owner:** [Your Name]
**Status:** Draft — Final Year Project

---

## 1. Overview

PayGuard is a payment processing platform (a scoped-down Razorpay/PayPal simulation) that lets a "merchant" accept payments through a REST API, while every transaction is scored in real time by a fraud-detection model. Flagged transactions surface in a review dashboard instead of auto-completing.

**Why this project:** It combines backend API design, distributed-systems concerns (idempotency, retries, webhooks), and applied ML in one coherent product — the three things payments/fintech and platform companies actually interview and hire for.

**Important scoping note:** No real money moves. There is no integration with an actual card network or bank. A `mock-processor` module simulates authorization/capture/decline outcomes. This keeps the project legal, safe, and buildable in a semester, while every surrounding system (API design, fraud, webhooks, auth) is built to production standards.

---

## 2. Goals & Objectives

| Goal | Why it matters |
|---|---|
| Build a correct, idempotent payment API | This is the single hardest-to-fake skill; interviewers probe it directly |
| Real-time fraud scoring on every transaction | Differentiates the project from a generic CRUD app |
| Reliable webhook delivery with retries | Demonstrates distributed-systems thinking (at-least-once delivery, backoff) |
| Merchant + Admin dashboard | Shows full-stack range, not just backend |
| Clean auth model (API keys + JWT) | Security fundamentals, table stakes for fintech-adjacent roles |

---

## 3. Target Users / Personas

1. **Merchant** — a business that integrates PayGuard's API into their checkout to accept payments. Interacts via API keys + a self-serve dashboard.
2. **Customer** — the end-payer completing a checkout (simulated card details, no real PII/PAN storage).
3. **Risk Analyst / Admin** — reviews transactions flagged by the fraud model, approves or blocks them.

---

## 4. Scope

### In scope (V1)
- Merchant signup, API key issuance
- Create / capture / refund payment via REST API
- Idempotency-key support on write endpoints
- Real-time fraud scoring (rule-based + ML model) on every payment
- Webhook system with signed payloads, retries, dead-letter handling
- Merchant dashboard: transactions, fraud alerts, API key & webhook management
- Admin view: review and resolve flagged transactions
- Rate limiting per API key

### Out of scope (V1)
- Real card network / bank integration
- Multi-currency, tax, or settlement/payout logic
- Mobile apps
- Multi-region / multi-tenant infra
- PCI-DSS-grade card storage (use tokenized mock card data only — **never handle real card numbers**)

### Possible V2 extensions (mention in your resume as "future work")
- Subscription/recurring billing
- 3-D Secure simulation
- Multi-merchant sub-account hierarchy (like Razorpay Route)

---

## 5. Assumptions & Constraints

- Solo or small-team build, ~10–14 week timeline alongside coursework.
- No real payment processor credentials — everything downstream of "authorization" is simulated.
- Fraud model trained on a public synthetic dataset (e.g., Kaggle's "Credit Card Fraud Detection" or IEEE-CIS Fraud Detection) — not real merchant data.
- Deployed on free/low-cost tiers (Render, Railway, Fly.io, or a single VM) — architecture should still *look* production-shaped even if the deployment is small.

---

## 6. Milestones (suggested)

| Week | Milestone |
|---|---|
| 1–2 | Finalize docs (this set), set up repo, DB schema, skeleton services |
| 3–4 | Core payment API: create/capture/refund + idempotency |
| 5 | Auth: API keys + JWT dashboard login |
| 6–7 | Fraud service: rules engine + baseline ML model, wire into payment flow |
| 8 | Webhook delivery service with retry/backoff |
| 9–10 | Dashboard: transactions, fraud review, analytics |
| 11 | Rate limiting, audit logging, hardening |
| 12 | Testing (unit + integration), load test the payment endpoint |
| 13 | Deployment, README, architecture diagram polish |
| 14 | Buffer / demo prep |

---

## 7. Success Criteria

- Payment API handles duplicate requests safely (same `Idempotency-Key` → same result, no double charge)
- Fraud model achieves reasonable precision/recall on held-out test data (document this — even "70% recall at 90% precision" is a legitimate, discussable number)
- Webhooks retry with exponential backoff and land in a dead-letter table after max attempts
- p95 latency on `POST /payments` stays low even with synchronous fraud pre-check (defer heavy scoring async if needed — see System Architecture doc)
- You can explain every design decision in an interview without notes

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Scope creep (trying to build "real Razorpay") | Stick to the in-scope list; log extensions as "future work" |
| Fraud model overfits to synthetic dataset | Be upfront about this limitation in your writeup — reviewers respect honesty over inflated claims |
| Running out of time before dashboard is polished | Backend correctness > UI polish for this audience; build dashboard last, keep it functional over fancy |
