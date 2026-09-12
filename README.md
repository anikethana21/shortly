# Shortly — URL Shortener Platform

> A production-grade, microservices-based URL shortener built with FastAPI, Next.js, MongoDB, Redis, and Kafka.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://shortly-frontend-h639.onrender.com)
[![API Gateway](https://img.shields.io/badge/API-gateway-blue)](https://shortly-api-gateway.onrender.com/health)

---

## 🌐 Live URLs

| Service | URL |
|---|---|
| **Frontend** | https://shortly-frontend-h639.onrender.com |
| **API Gateway** | https://shortly-api-gateway.onrender.com |
| **API Docs** | https://shortly-api-gateway.onrender.com/docs |

---

## 🏗️ Architecture

```
                    ┌─────────────┐
                    │   Frontend  │  Next.js 14 (App Router)
                    └──────┬──────┘
                           │ HTTPS
                    ┌──────▼──────┐
                    │ API Gateway │  FastAPI reverse proxy
                    └──────┬──────┘
               ┌───────────┴───────────┐
        ┌──────▼──────┐        ┌───────▼───────┐
        │ Link Service│        │Redirect Service│
        │  (port 8001)│        │  (port 8002)  │
        └──────┬──────┘        └───────┬───────┘
               │                       │
        ┌──────▼───────────────────────▼──────┐
        │           MongoDB (Atlas)            │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │           Redis (Upstash)            │
        └──────────────────┬──────────────────┘
                           │ Kafka events
        ┌──────────────────▼──────────────────┐
        │         Redpanda (Kafka)             │
        └──┬─────────────────────┬────────────┘
           │                     │
  ┌────────▼────────┐   ┌────────▼────────┐   ┌─────────────────┐
  │Analytics Consumer│  │Verification     │   │ Cleanup Service  │
  │  (Kafka worker)  │  │Worker           │   │ (expired links)  │
  └──────────────────┘  └─────────────────┘   └─────────────────┘
```

### Services

| Service | Stack | Role |
|---|---|---|
| **api-gateway** | FastAPI + httpx | Single public entrypoint, reverse proxies to all services |
| **link-service** | FastAPI + Motor | Create, manage, and list short links |
| **redirect-service** | FastAPI + Motor | Handle `/{code}` redirects, track click analytics |
| **analytics-consumer** | Python + AIOKafka | Consumes click events from Kafka, writes to MongoDB |
| **verification-worker** | Python + AIOKafka | Verifies long URLs are reachable |
| **cleanup-service** | Python + Motor | Periodically deletes expired links |
| **frontend** | Next.js 14 + TypeScript | React UI — shorten, manage links, view QR codes |

---

## ⚡ Features

- 🔗 **Short link creation** with optional custom codes and expiry
- 📲 **QR code generation** for every short link
- 📊 **Analytics** — click counts and clicks by date
- ✅ **Link verification** — background worker checks if destination is reachable
- 🧹 **Auto-cleanup** — expired links are purged automatically
- 🔐 **Owner tokens** — manage your own links without accounts
- ⚡ **Redis caching** — redirect lookups served from cache

---

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for local Mongo/Redis/Kafka)

### Environment Variables

Create a `.env` file at the project root:

```env
# MongoDB
MONGO_URL=mongodb+srv://<user>:<password>@cluster0.fymql83.mongodb.net/shortly

# Redis (Upstash TLS)
REDIS_URL=rediss://default:<password>@<host>.upstash.io:6379

# Kafka (Redpanda)
KAFKA_BOOTSTRAP_SERVERS=<broker>.redpanda.com:9092
KAFKA_USERNAME=<username>
KAFKA_PASSWORD=<password>

# Public URL of the API Gateway
BASE_URL=http://localhost:8000
```

### Run a Service Locally

```bash
cd services/link-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Run the Frontend Locally

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

---

## 🚀 Deployment (Render)

All services are deployed on [Render](https://render.com) as Web Services.

Each service needs these env vars set in the Render dashboard:

| Variable | Description |
|---|---|
| `MONGO_URL` | MongoDB Atlas connection string |
| `REDIS_URL` | Upstash Redis TLS URL |
| `KAFKA_BOOTSTRAP_SERVERS` | Redpanda broker address |
| `KAFKA_USERNAME` / `KAFKA_PASSWORD` | Redpanda SASL credentials |
| `BASE_URL` | Public URL of the API gateway |
| `LINK_SERVICE_URL` | Internal URL of link-service (gateway only) |
| `REDIRECT_SERVICE_URL` | Internal URL of redirect-service (gateway only) |
| `NEXT_PUBLIC_API_URL` | API gateway URL baked into the Next.js build (frontend only) |

### Build & Start Commands

| Service | Build Command | Start Command |
|---|---|---|
| FastAPI services | `pip install -r requirements.txt` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | `npm install && npm run build` | `npm start` |

---

## 📁 Project Structure

```
shortly/
├── services/
│   ├── api-gateway/          # Reverse proxy
│   ├── link-service/         # Link CRUD + QR
│   ├── redirect-service/     # Redirect + analytics tracking
│   ├── analytics-consumer/   # Kafka consumer
│   ├── verification-worker/  # URL health checker
│   └── cleanup-service/      # Expired link janitor
├── frontend/                 # Next.js 14 app
│   └── src/
│       ├── app/              # App Router pages
│       ├── components/       # React components
│       └── lib/api.ts        # API client
└── .env                      # Local secrets (not committed)
```

---

## 🔌 API Reference

All requests go through the **API Gateway** at `https://shortly-api-gateway.onrender.com`.

### Create a Short Link

```http
POST /api/links
Content-Type: application/json
X-Owner-Token: <your-token>

{
  "long_url": "https://example.com",
  "custom_code": "my-link",       // optional
  "expires_in_minutes": 1440      // optional
}
```

**Response 201:**
```json
{
  "short_code": "abc123",
  "short_url": "https://shortly-api-gateway.onrender.com/abc123",
  "long_url": "https://example.com",
  "qr_code_base64": "...",
  "created_at": "2026-09-12T00:00:00Z",
  "expires_at": null,
  "is_custom": false,
  "verified": "pending",
  "owner_token": "..."
}
```

### Redirect

```http
GET /{short_code}
→ 302 Location: https://example.com
```

### Get Analytics

```http
GET /api/analytics/{short_code}
X-Owner-Token: <your-token>
```

### List My Links

```http
GET /api/links/mine
X-Owner-Token: <your-token>
```

---

## 🧑‍💻 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Motor (async MongoDB), AIOKafka |
| Frontend | Next.js 14, TypeScript, React |
| Database | MongoDB Atlas |
| Cache | Upstash Redis (TLS) |
| Messaging | Redpanda (Kafka-compatible) |
| Hosting | Render (free tier) |

---

## 📝 License

MIT
