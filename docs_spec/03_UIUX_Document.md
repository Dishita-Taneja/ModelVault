# UI/UX Document
## PayGuard Dashboard

This covers the merchant/admin dashboard — the only human-facing surface in the product (the payment API itself has no UI, only a mock checkout widget for demo purposes).

---

## 1. Design Principles

- **Data-dense, not decorative.** This is an ops tool for merchants and risk analysts, not a marketing site. Prioritize scanability (tables, badges, sparklines) over large hero sections.
- **Status is always visible.** Every payment/webhook/transaction has a color-coded status badge, consistent across every screen it appears on.
- **No dead ends.** Every empty state (no transactions yet, no API keys yet) has a clear next action.

---

## 2. Information Architecture / Sitemap

```
/login
/signup
/dashboard                     (overview: volume, approval rate, fraud rate, recent activity)
/transactions                  (list + filters)
/transactions/:id               (detail: timeline, fraud score breakdown, actions)
/fraud-review                  (queue of flagged transactions, admin/risk-analyst role)
/webhooks                      (list, add endpoint, delivery logs)
/api-keys                      (list, generate, revoke)
/settings                      (business profile, team members)
/checkout-demo                 (a mock checkout page to demonstrate the customer-facing flow)
```

---

## 3. Key Screens

### 3.1 Dashboard Overview
- Top: 4 stat cards — Total Volume (30d), Approval Rate, Fraud Rate, Active Alerts
- Middle: line chart of transaction volume over time
- Bottom: table of 10 most recent transactions with status badges
- Empty state (new merchant): "No transactions yet" + a code snippet showing the first API call to make

### 3.2 Transactions List
- Filter bar: status (all/authorized/captured/flagged/failed/refunded), date range, amount range, search by customer email/transaction ID
- Table columns: ID, Customer, Amount, Status, Risk Score, Created At
- Risk score shown as a small colored bar (green <0.3, amber 0.3–0.7, red >0.7) — makes fraud-worthy rows scannable at a glance
- Row click → transaction detail

### 3.3 Transaction Detail
- Header: amount, status badge, customer info
- **Event timeline** (vertical, chronological): created → fraud check → authorized → captured, each with a timestamp — this is the single most interview-relevant screen since it visualizes the state machine
- **Fraud score panel**: score, threshold used, top contributing factors (e.g. "unusual amount for this customer," "new device," "high velocity") — even a simple feature-importance readout is enough
- Actions (contextual to status): Capture, Refund, Approve (if flagged), Block (if flagged)
- Raw JSON tab — showing the raw API object builds credibility that this isn't just a mocked-up UI

### 3.4 Fraud Review Queue
- List sorted by risk score descending, newest first as tiebreaker
- Bulk-select not required for V1 — one-at-a-time review is fine
- Each row expands inline to show the same fraud score panel as the detail view, with Approve/Block buttons directly in the row (minimize clicks for the reviewer)

### 3.5 Webhooks
- List of registered endpoints with subscribed event types and health status (last delivery success/fail)
- "Add endpoint" form: URL, event type checkboxes, generates a signing secret shown once
- Delivery log per endpoint: timestamp, event type, HTTP status returned, attempt number, "Replay" button for dead-lettered deliveries

### 3.6 API Keys
- Table: key ID (masked, e.g. `pk_live_••••4f2a`), mode (test/live), created date, last used, status
- "Generate new key" → modal shows the secret once with a copy button and a clear warning it won't be shown again
- Revoke action with confirmation dialog

### 3.7 Checkout Demo (customer-facing)
- Single-page mock checkout: amount, mock card fields (card number/expiry/CVV — clearly labeled as test data, e.g. prefilled `4242 4242 4242 4242`), Pay button
- On submit → calls your own `/v1/payments` API, then shows success/failure/pending-review state
- This screen exists purely so you can demo the end-to-end flow live in an interview

---

## 4. Core User Flows

**Merchant integration flow:** Signup → generate test API key → copy code snippet → make first test payment via curl/Postman → see it appear in dashboard.

**Fraud review flow:** Payment created → sync rules pass → async ML score returns 0.82 → status flips to `flagged`, webhook fires `payment.flagged` → analyst opens Fraud Review Queue → inspects score breakdown → clicks Approve → status flips to `captured`, webhook fires `payment.captured`.

**Webhook debugging flow:** Merchant's endpoint is down → deliveries fail 5 times with backoff → marked dead-letter → merchant fixes their server → clicks Replay → delivery succeeds.

---

## 5. Visual System (keep simple, don't over-invest here)

- **Typography:** one clean system font stack (Inter/system-ui) — don't spend time on custom fonts
- **Color:** neutral gray base, one accent color for primary actions, semantic colors for status (green=success, amber=pending/flagged, red=failed/blocked, gray=neutral)
- **Components:** a small consistent set — status badge, data table, stat card, timeline item, side modal for forms. Reuse these everywhere rather than designing each screen bespoke.
- **Responsiveness:** desktop-first is acceptable (this is an ops dashboard, not a consumer app) but make sure tables scroll horizontally on smaller screens rather than breaking layout.

---

## 6. What to skip

Don't build: dark mode, multi-language support, elaborate onboarding tours, drag-and-drop anything. None of this is what gets evaluated — a clean, functional, consistent dashboard is enough. Spend the saved time on the fraud detail panel and the transaction timeline; those are the screens that actually demonstrate system understanding.
