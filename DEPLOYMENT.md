# Deployment Guide

Step-by-step instructions for deploying the platform to Railway (backend + frontend)
with Neon pgvector and Railway Redis.

---

## Architecture Overview (Production/Demo)

```
Railway Project
├── Service: api         ← FastAPI backend (this repo root Dockerfile)
├── Service: frontend    ← Next.js demo UI (frontend/Dockerfile)
└── Add-on: Redis        ← Railway managed Redis
Neon (external)          ← PostgreSQL with pgvector extension
```

---

## Prerequisites

- Railway account (Hobby plan or above)
- Neon account (free tier is sufficient)
- OpenRouter API key — free at https://openrouter.ai
- GitHub repo connected to Railway

---

## Step 1: Neon Database Setup

1. Create a new Neon project at https://console.neon.tech
2. Copy the connection string from **Dashboard → Connection Details → Connection string**
   - Format: `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`
3. Enable the pgvector extension (run once in the Neon SQL editor):
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. The `document_chunks` table and index are created automatically on first startup.

---

## Step 2: Deploy the Backend to Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select `faiz-faruqi/local-first-hybrid-ai-platform`
3. Railway will detect `railway.toml` in the repo root and use the backend Dockerfile
4. Add the **Redis** add-on: **+ Add Service → Database → Redis**
5. Set the following environment variables on the `api` service:

```
DEMO_MODE=true
VECTOR_STORE=pgvector
DATABASE_URL=<paste-neon-connection-string>
REDIS_URL=${{Redis.REDIS_URL}}         ← Railway injects this automatically
OPENROUTER_API_KEY=<your-key>
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
EMBEDDING_MODEL=all-MiniLM-L6-v2
ADMIN_KEY=<generate-a-secure-random-string>
LOG_LEVEL=info
CACHE_TTL_SECONDS=3600
```

6. Deploy. The health check at `/health` will confirm readiness.
7. Set a custom domain (optional): **Settings → Custom Domain → your domain**.

---

## Step 3: Deploy the Frontend to Railway

1. In the same Railway project, add a new service: **+ Add Service → GitHub Repo**
2. Select the same repo
3. In service settings, change the **Root Directory** to `frontend/`
   - Railway will use `frontend/Dockerfile` (detected via `frontend/railway.toml`)
4. Set environment variables:

```
NEXT_PUBLIC_API_URL=https://<your-backend-railway-url>
```

5. Deploy. Visit the frontend URL to verify.
6. Set custom domain for the frontend: **Settings → Custom Domain**.

---

## Step 4: Seed the Demo Documents

After both services are deployed and healthy:

```bash
# From your local machine (requires Python 3.11+ and requests installed)
python scripts/seed_demo.py --api-url https://api.yourdomain.com
```

This ingests the 5 synthetic vendor contracts from `sample-docs/` into Neon pgvector.
The script is idempotent-safe — re-running adds more chunks but does not delete existing ones.

To verify seeding worked:
```bash
python scripts/health_check.py --api-url https://api.yourdomain.com
```

---

## Step 5: Verify the Demo

1. Open the frontend URL in a browser
2. Submit a sample query: *"What are the termination conditions in the vendor contracts?"*
3. Verify:
   - A response is returned with source documents listed
   - The `LOCAL` badge appears (first query)
   - Submit the same query again — the `CACHED` badge and <10ms latency confirm Redis is working
   - Enable "Force cloud fallback" toggle and submit — the `CLOUD` badge should appear
   - The architecture diagram highlights the active node after each query

---

## Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DEMO_MODE` | Yes | `true` on Railway — routes both tiers through OpenRouter |
| `VECTOR_STORE` | Yes | `pgvector` for Railway, `qdrant` for local dev |
| `DATABASE_URL` | If pgvector | Neon connection string with `sslmode=require` |
| `REDIS_URL` | If Railway | Full Redis connection string (from Railway add-on) |
| `REDIS_HOST` + `REDIS_PORT` | If local | Used when `REDIS_URL` is not set |
| `OPENROUTER_API_KEY` | Yes | Free key from openrouter.ai |
| `OPENROUTER_MODEL` | Yes | `mistralai/mistral-7b-instruct` for demo |
| `OLLAMA_BASE_URL` | No (local only) | Ollama endpoint for on-premises inference |
| `OLLAMA_MODEL` | No (local only) | `gemma2:9b` for production |
| `EMBEDDING_MODEL` | No | Default: `all-MiniLM-L6-v2` |
| `ADMIN_KEY` | Yes | Required for `DELETE /ingest/flush-cache` |
| `CACHE_TTL_SECONDS` | No | Default: 3600 (1 hour) |
| `LOG_LEVEL` | No | Default: `info` |
| `NEXT_PUBLIC_API_URL` | Frontend | Backend URL for the Next.js app |

---

## Local Development

For local development with Docker Compose (uses Qdrant + Redis, no Neon):

```bash
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY at minimum
docker compose up -d
python scripts/ingest_documents.py --input-dir ./sample-docs
# API: http://localhost:8000
# Frontend: cd frontend && npm install && npm run dev → http://localhost:3000
```

---

## Flushing the Cache

To flush all cached LLM responses (e.g. after re-ingesting documents):

```bash
curl -X DELETE https://api.yourdomain.com/ingest/flush-cache \
  -H "X-Admin-Key: your-admin-key"
```
