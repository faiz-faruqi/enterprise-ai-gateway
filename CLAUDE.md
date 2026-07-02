# CLAUDE.md — Local-First Hybrid AI Platform

This file provides context for AI coding agents (Claude Code / Kilo) working on this repository.

---

## What This Project Is

A **production-style GenAI platform** demonstrating enterprise document intelligence architecture.
It is both a working system and a portfolio artefact showcasing:

- Hybrid inference routing (local-first with cloud fallback)
- Retrieval-Augmented Generation (RAG) over private documents
- Semantic response caching (Redis) for cost control
- Clean architectural separation of concerns (orchestration / retrieval / inference / cache)

**Repository:** https://github.com/faiz-faruqi/local-first-hybrid-ai-platform  
**Live demo:** Deployed on Railway. See `DEPLOYMENT.md` for setup.

---

## Architecture (brief)

```
User Query → FastAPI Control Plane
               ├── Embedder (SentenceTransformers all-MiniLM-L6-v2)
               ├── Vector Store (Qdrant local | Neon pgvector on Railway)
               │     └── Returns top-k semantically relevant chunks
               ├── Redis Cache
               │     ├── HIT  → return immediately, zero LLM cost
               │     └── MISS → route to inference
               └── InferenceRouter
                     ├── PRIMARY  → OllamaClient (local, Gemma 2 9B)
                     └── FALLBACK → OpenRouterClient (cloud, GPT-4o-mini)
```

Full architecture diagram: `docs/architecture/architecture-overview.md`  
Architecture Decision Records: `docs/adr/`

---

## Repository Structure

```
.
├── src/
│   ├── api/
│   │   ├── main.py                  ← FastAPI app, CORS, router registration
│   │   ├── dependencies.py          ← Singleton FastAPI dependencies (Depends)
│   │   └── routers/
│   │       ├── query.py             ← POST /query/ — core RAG pipeline
│   │       └── ingest.py            ← POST /ingest/text, DELETE /ingest/flush-cache
│   ├── inference/
│   │   ├── router.py                ← Local-first routing logic
│   │   ├── ollama_client.py         ← Async Ollama /api/generate client
│   │   └── openrouter_client.py     ← Async OpenRouter completions client
│   ├── retrieval/
│   │   ├── embedder.py              ← SentenceTransformer embedding wrapper
│   │   ├── qdrant_client.py         ← Qdrant async vector store (local dev)
│   │   ├── pgvector_client.py       ← pgvector async vector store (Railway/Neon)
│   │   └── vector_store_factory.py  ← Switches backend via VECTOR_STORE env var
│   ├── cache/
│   │   └── redis_cache.py           ← MD5-keyed async Redis cache
│   └── models/
│       └── schemas.py               ← Pydantic v2 request/response schemas
├── frontend/                        ← Next.js 14 demo UI
│   ├── src/app/page.tsx             ← Main demo page
│   ├── src/components/
│   │   ├── ChatPanel.tsx            ← Chat interface
│   │   ├── ArchDiagram.tsx          ← SVG architecture with live highlighting
│   │   ├── ResponseMeta.tsx         ← Provider badge, latency, cache pill
│   │   └── SourceDocs.tsx           ← Collapsible source document list
│   └── src/lib/api.ts               ← Typed fetch wrapper
├── scripts/
│   ├── ingest_documents.py          ← CLI ingestion from local files
│   ├── seed_demo.py                 ← Seeds sample-docs via HTTP API
│   └── health_check.py              ← Component health verification
├── tests/
│   ├── conftest.py
│   ├── test_inference_router.py
│   ├── test_cache.py
│   ├── test_embedder.py
│   └── test_query_endpoint.py
├── sample-docs/                     ← 5 synthetic vendor contracts (demo corpus)
├── docs/
│   ├── architecture/
│   ├── adr/
│   └── runbooks/
├── Dockerfile                       ← Backend container
├── docker-compose.yml               ← Local dev (Qdrant + Redis + Open WebUI)
├── railway.toml                     ← Backend Railway deploy config
└── .env.example                     ← All environment variables documented
```

---

## Local Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ (for frontend)
- Ollama installed locally (optional — cloud fallback works without it)

### 1. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set OPENROUTER_API_KEY
```

### 2. Start backend services
```bash
docker compose up -d
# Starts: FastAPI (8000), Qdrant (6333), Redis (6379), Open WebUI (3000)
```

### 3. Ingest sample documents
```bash
pip install -r src/requirements.txt
python scripts/ingest_documents.py --input-dir ./sample-docs
# Or via the seed script (requires API to be running):
python scripts/seed_demo.py --api-url http://localhost:8000
```

### 4. Test the API
```bash
curl -X POST http://localhost:8000/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the termination conditions?", "top_k": 5}'
```

### 5. Run the frontend (dev mode)
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 6. Run tests
```bash
pytest tests/ -v
```

---

## Railway Demo Deployment

See `DEPLOYMENT.md` for the full step-by-step guide. Summary:

**Backend service env vars (Railway):**
```
DEMO_MODE=true
VECTOR_STORE=pgvector
DATABASE_URL=<neon-connection-string>
REDIS_URL=<railway-redis-url>
OPENROUTER_API_KEY=<your-key>
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
ADMIN_KEY=<secure-random-string>
```

**Frontend service env vars (Railway):**
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**After deploy, seed the database:**
```bash
python scripts/seed_demo.py --api-url https://api.yourdomain.com
```

---

## Known Issues / Gotchas

### 1. Ollama `await` bug (FIXED in v0.2.0)
The original `ollama_client.py` was missing `await` on the `client.post()` call inside an `async with` block. This caused all local inference to silently fail and always fall through to cloud. Fixed in `src/inference/ollama_client.py`.

### 2. Redis URL vs host/port
Railway's Redis add-on provides a single `REDIS_URL` connection string, not separate host/port. The `ResponseCache` now accepts either pattern — `REDIS_URL` takes priority when set.

### 3. pgvector SSL on Neon
All Neon connections require `sslmode=require`. The `PgVectorStore` hardcodes `ssl="require"` in the asyncpg pool. If you see `SSL required` errors, ensure your `DATABASE_URL` includes `?sslmode=require`.

### 4. pgvector index creation
The IVFFlat index (`CREATE INDEX ... USING ivfflat`) requires at least 100 rows to be useful. For the demo with ~50 chunks, it creates the index anyway — it will work but cosine search will fall back to sequential scan for small datasets.

### 5. Demo mode model label
In `DEMO_MODE=true`, the frontend displays a banner noting that the "local" node uses `mistral-7b-instruct` via OpenRouter rather than the production `gemma2:9b` on-premises. This is honest labeling — do not remove it.

### 6. Module-level singleton instantiation removed
`src/api/routers/query.py` previously created `_embedder`, `_vector_store`, etc. at module import time. This caused errors on startup if services were unreachable. These are now FastAPI `Depends()` singletons in `src/api/dependencies.py`.

---

## Test Strategy

| Layer | Approach |
|-------|----------|
| `InferenceRouter` | Unit tests with `AsyncMock` — no real LLM calls |
| `ResponseCache` | Unit tests with mocked `aioredis.Redis` |
| `Embedder` | Unit tests — real model loaded (fast, ~384-dim outputs) |
| `PgVectorStore` | Integration tests require `DATABASE_URL` (skipped in CI without it) |
| Query endpoint | Integration-style via FastAPI `TestClient` with all externals mocked |

Run tests:
```bash
pytest tests/ -v                        # all tests
pytest tests/ -v -k "not integration"  # skip integration tests
```

---

## Code Style

- **Python 3.11+** — use `list[...]`, `dict[...]`, `X | Y` union syntax throughout
- **Async-first** — all I/O operations use `async`/`await`; never `asyncio.run()` inside FastAPI routes
- **Pydantic v2** — use `model_validate`, `model_dump` (not v1 `.dict()`)
- **Ruff** for linting and formatting: `ruff check src/ scripts/` and `ruff format src/ scripts/`
- **Line length**: 100 characters

---

## Do Not

- Do not commit `.env` to version control
- Do not call `asyncio.run()` inside FastAPI route handlers
- Do not add Ollama as a Railway service — it requires GPU and large model weights
- Do not use `qdrant_client.models.ScoredPoint` in pgvector code — use `ScoredChunk` dataclass
- Do not hardcode API keys or secrets anywhere in source files
- Do not remove the demo mode banner from `ArchDiagram.tsx` — it is required for honest disclosure
