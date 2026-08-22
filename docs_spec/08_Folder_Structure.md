# Folder Structure
## PayGuard

A monorepo containing three services + shared infra. This layout is intentionally explicit about boundaries — it should be obvious from the tree alone which service owns what.

```
payguard/
├── docs/                                # this document set lives here in the repo
│   ├── 01_PRD.md
│   ├── 02_Feature_Specification.md
│   ├── 03_UIUX_Document.md
│   ├── 04_System_Architecture.md
│   ├── 05_Database_Design.md
│   ├── 06_API_Documentation.md
│   ├── 07_Authentication.md
│   └── 08_Folder_Structure.md
│
├── payment-service/                     # Core Payment API — Node.js + TypeScript
│   ├── src/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   │   ├── auth.controller.ts
│   │   │   │   ├── auth.service.ts
│   │   │   │   ├── jwt.strategy.ts
│   │   │   │   └── auth.types.ts
│   │   │   ├── api-keys/
│   │   │   │   ├── api-keys.controller.ts
│   │   │   │   └── api-keys.service.ts
│   │   │   ├── payments/
│   │   │   │   ├── payments.controller.ts
│   │   │   │   ├── payments.service.ts
│   │   │   │   ├── payments.state-machine.ts
│   │   │   │   └── payments.types.ts
│   │   │   ├── refunds/
│   │   │   │   ├── refunds.controller.ts
│   │   │   │   └── refunds.service.ts
│   │   │   ├── fraud/
│   │   │   │   ├── fraud.rules.ts          # synchronous rules layer
│   │   │   │   └── fraud.client.ts         # calls fraud-service over HTTP/queue
│   │   │   ├── webhooks/
│   │   │   │   ├── webhooks.controller.ts
│   │   │   │   └── webhooks.service.ts
│   │   │   └── merchants/
│   │   │       ├── merchants.controller.ts
│   │   │       └── merchants.service.ts
│   │   ├── middleware/
│   │   │   ├── auth-api-key.middleware.ts
│   │   │   ├── auth-jwt.middleware.ts
│   │   │   ├── idempotency.middleware.ts
│   │   │   ├── rate-limit.middleware.ts
│   │   │   └── error-handler.middleware.ts
│   │   ├── db/
│   │   │   ├── migrations/
│   │   │   ├── models/                     # or Prisma schema.prisma
│   │   │   └── client.ts
│   │   ├── queue/
│   │   │   ├── publisher.ts
│   │   │   └── events.ts                   # event type definitions
│   │   ├── config/
│   │   │   └── index.ts                    # env var loading/validation
│   │   ├── utils/
│   │   │   ├── logger.ts                   # scrubs secrets before logging
│   │   │   └── crypto.ts                   # hashing, HMAC helpers
│   │   ├── app.ts
│   │   └── server.ts
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── .env.example
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── fraud-service/                       # Fraud Scoring — Python + FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   └── score.py                    # POST /score endpoint (or queue consumer)
│   │   ├── model/
│   │   │   ├── model.pkl                   # trained model artifact
│   │   │   ├── features.py                 # feature extraction logic
│   │   │   └── predict.py
│   │   ├── consumer/
│   │   │   └── queue_consumer.py           # listens for payment-created events
│   │   ├── config.py
│   │   └── main.py
│   ├── training/
│   │   ├── data/                           # (gitignored) dataset used for training
│   │   ├── train_model.py
│   │   ├── evaluate_model.py
│   │   └── notebook.ipynb                  # exploratory analysis, keep for your writeup
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── webhook-service/                     # Webhook delivery worker — Node.js
│   ├── src/
│   │   ├── consumer.ts                     # consumes status-change events
│   │   ├── deliver.ts                      # signs + sends payloads
│   │   ├── retry-scheduler.ts              # exponential backoff logic
│   │   └── dead-letter.ts
│   ├── package.json
│   └── Dockerfile
│
├── dashboard/                            # React + TypeScript SPA
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── DashboardOverview.tsx
│   │   │   ├── Transactions.tsx
│   │   │   ├── TransactionDetail.tsx
│   │   │   ├── FraudReview.tsx
│   │   │   ├── Webhooks.tsx
│   │   │   ├── ApiKeys.tsx
│   │   │   └── CheckoutDemo.tsx
│   │   ├── components/
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── Timeline.tsx
│   │   │   └── FraudScorePanel.tsx
│   │   ├── api/
│   │   │   └── client.ts                   # typed API client, wraps fetch
│   │   ├── hooks/
│   │   ├── store/                          # auth/session state
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── infra/
│   ├── docker-compose.yml                 # spins up all services + postgres + redis locally
│   ├── nginx/
│   │   └── nginx.conf                      # optional: reverse proxy in front of services
│   └── k8s/                               # optional stretch: deployment manifests
│       ├── payment-service.yaml
│       ├── fraud-service.yaml
│       └── webhook-service.yaml
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Notes on this structure

- **Each service has its own `package.json`/`requirements.txt` and `Dockerfile`** — they're independently runnable and deployable, even though they live in one repo. This is a legitimate "monorepo with service boundaries" pattern, worth naming as such.
- **`fraud-service` is Python, everything else is Node/TypeScript** — deliberately polyglot. It's a genuine reason to use Python (ML ecosystem) rather than forcing one language everywhere, and it's a natural interview talking point ("why is one service in a different language").
- **`docs/` ships in the repo, not just in your head** — when someone (recruiter, interviewer, or future you) opens the repo, the README should link straight to these documents.
- Start by scaffolding `payment-service` + `infra/docker-compose.yml` first — everything else can be stubbed until the core payment API and idempotency logic are solid.
