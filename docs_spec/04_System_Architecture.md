# System Architecture
## PayGuard

---

## 1. Architecture Style

Service-oriented, not a monolith, but not over-fragmented microservices either. Three deployable services + shared infra. This is the right size to talk about "why I split it this way" in an interview without drowning in operational complexity.

```
                                   ┌─────────────────────┐
                                   │   Merchant Server    │
                                   │ (calls PayGuard API) │
                                   └──────────┬───────────┘
                                              │ HTTPS + API Key
                                              ▼
┌───────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                        │
│   - TLS termination                                              │
│   - Auth (API key / JWT) middleware                              │
│   - Rate limiting (Redis-backed sliding window)                  │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Core Payment       │◄──────────────┐
                 │   Service (Node/TS)  │                │
                 │  - Payments CRUD     │                │
                 │  - Idempotency layer │                │
                 │  - Sync fraud rules  │                │
                 │  - State machine     │                │
                 └──────┬───────┬───────┘                │
                        │       │                         │
        publishes event │       │ reads/writes            │ admin actions
                        ▼       ▼                         │
              ┌─────────────┐ ┌──────────────┐   ┌────────┴────────┐
              │ Message      │ │  PostgreSQL   │   │  Dashboard API   │
              │ Queue        │ │  (primary DB) │   │  (same service   │
              │ (Redis       │ └──────────────┘   │  or separate     │
              │  Streams)    │                     │  BFF layer)      │
              └───┬─────┬────┘                     └────────┬────────┘
                  │     │                                    │
      ┌───────────┘     └───────────┐                        ▼
      ▼                             ▼                 ┌──────────────┐
┌───────────────┐           ┌───────────────┐         │  React        │
│ Fraud Scoring  │           │ Webhook        │         │  Dashboard SPA │
│ Service        │           │ Delivery       │         └──────────────┘
│ (Python/FastAPI)│           │ Service        │
│ - ML model      │           │ (Node worker)  │
│ - writes score  │           │ - retry/backoff│
│   back to DB    │           │ - dead-letter  │
└───────────────┘           └───────────────┘
```

---

## 2. Components

| Component | Responsibility | Tech |
|---|---|---|
| API Gateway / Auth Middleware | TLS, request auth, rate limiting | Express/NestJS middleware (or standalone if you want a dedicated component) |
| Core Payment Service | Payment state machine, idempotency, synchronous fraud rules, exposes REST API | Node.js + TypeScript (Express or NestJS) |
| Fraud Scoring Service | Consumes payment-created events, runs ML model, writes risk score back | Python + FastAPI, scikit-learn/XGBoost |
| Webhook Delivery Service | Consumes status-change events, delivers signed payloads, retry/backoff, dead-letter | Node.js worker process |
| Message Queue | Decouples the payment API from slow/async work (ML scoring, webhook delivery) so `POST /payments` stays fast | Redis Streams (simple) or RabbitMQ (if you want message-broker experience) |
| PostgreSQL | System of record — money-related data needs ACID guarantees, not eventual consistency | PostgreSQL |
| Redis | Idempotency key cache, rate-limit counters, queue | Redis |
| Dashboard SPA | Merchant/admin UI | React + TypeScript, Tailwind |

---

## 3. Why async fraud scoring, not fully synchronous

This is the single most important design decision in the project, and the one most worth explaining in an interview:

- Running a full ML inference inline on every `POST /payments` call adds latency and a hard dependency — if the fraud service is slow or down, payments shouldn't fail.
- Instead: a **fast synchronous rules layer** (a handful of cheap checks — amount thresholds, velocity, blocklist) runs inline and can outright block obvious fraud in milliseconds.
- Anything that passes the rules layer is authorized optimistically, then an event is published to the queue. The **async ML layer** scores it within ~1–2 seconds and can still flip a `captured` payment to `flagged` before final settlement, since capture in this design isn't instantaneous either.
- This is the same pattern real payment processors use: authorize fast, review deeper, hold final settlement for the small flagged minority.

---

## 4. Sequence: Create Payment (happy path + fraud flag)

```
Merchant Server        Payment Service        Redis          Queue         Fraud Service        Webhook Service
     │  POST /payments        │                  │              │                │                    │
     │  + Idempotency-Key ───►│                  │               │                │                    │
     │                        │  check idem key ►│               │                │                    │
     │                        │◄── not found ─────│               │                │                    │
     │                        │  run sync rules   │               │                │                    │
     │                        │  (pass)           │               │                │                    │
     │                        │  write payment    │               │                │                    │
     │                        │  (status=authorized)              │                │                    │
     │                        │  cache response ─►│               │                │                    │
     │◄── 201 authorized ─────│                   │               │                │                    │
     │                        │  publish event ───────────────────►                │                    │
     │                        │                                    │  consume ─────►│                    │
     │                        │                                    │                │  score = 0.85       │
     │                        │                                    │                │  write to DB         │
     │                        │                                    │                │  status=flagged      │
     │                        │                                    │                │  publish event ──────►
     │                        │                                    │                │                     │ deliver webhook
     │                        │                                    │                │                     │ payment.flagged
     │◄─────────────────────────────────────  (async, minutes later) webhook to merchant's registered URL
```

---

## 5. Reliability & Scalability Notes (talk about these even if you don't fully implement all of them)

- **Idempotency** prevents duplicate charges on retry — non-negotiable for a payment API.
- **At-least-once webhook delivery** with retries means merchants may receive duplicate events — document that merchants should also treat their webhook handler as idempotent (this is a real, correct point to make in an interview).
- **Horizontal scaling:** the Core Payment Service is stateless (state lives in Postgres/Redis), so it can run multiple instances behind a load balancer.
- **Read/write split (optional stretch):** dashboard read-heavy queries (analytics, transaction lists) could hit a read replica so they never compete with write throughput on the payment path.
- **Backpressure:** if the fraud queue backs up, payments should still complete (rules-layer-only) rather than blocking — degrade gracefully, don't fail the customer's checkout because your ML service is slow.

---

## 6. Deployment (V1, kept simple)

- Docker Compose locally: `payment-service`, `fraud-service`, `webhook-service`, `dashboard`, `postgres`, `redis`
- Deploy target: Render/Railway/Fly.io (free/low-cost tiers) for a live demo link, or a single Docker host if budget is zero
- Optional stretch: containerize with a basic Kubernetes manifest even if you don't run a real cluster — having the YAML and being able to explain it is a legitimate talking point for Microsoft/ServiceNow-style infra questions
