# Local-First Hybrid AI Platform

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Status](https://img.shields.io/badge/Status-Portfolio%20Project-orange)

A production-style GenAI platform for **enterprise document intelligence** that combines retrieval-augmented generation (RAG), local inference, cloud fallback, and semantic response caching.

Built as an architecture portfolio artefact demonstrating patterns relevant to:

- Enterprise AI Architect
- GenAI Solution Architect
- Data Platform Architect
- Cloud AI Transformation Lead

---

## Problem Statement

Enterprises want AI-assisted answers over internal documents without routing sensitive content to external model providers, while also managing unpredictable per-token cloud costs.

This platform addresses that by combining:

- **Local-first inference** (Ollama / Gemma 2) for privacy-sensitive workloads
- **Cloud fallback** (OpenRouter) for resilience and higher-complexity reasoning
- **Semantic response caching** (Redis) to eliminate redundant model calls
- **Vector retrieval** (Qdrant) to ground answers in enterprise content only
- **Decoupled control and inference planes** for flexible deployment topology

---

## Architecture

```mermaid
flowchart LR
    User[Business User]
    UI[Open WebUI]
    API[FastAPI Orchestrator]
    Redis[Redis Cache]
    Embed[SentenceTransformers]
    Qdrant[Qdrant Vector DB]
    Docs[Enterprise Documents]
    Ollama["Ollama Local LLM\n(Windows Node)"]
    OpenRouter[OpenRouter Cloud LLM]
    n8n[n8n Workflows]

    User --> UI
    UI --> API
    n8n --> API

    Docs --> API
    API --> Embed
    Embed --> Qdrant
    API --> Qdrant
    Qdrant --> API

    API --> Redis
    Redis --> API

    API -->|Primary| Ollama
    API -->|Fallback| OpenRouter
    Ollama --> API
    OpenRouter --> API

    API --> UI
```

### Request flow

```
User Query
  └─► FastAPI (embed query)
        └─► Qdrant (retrieve top-k chunks)
              └─► Redis (cache lookup)
                    ├─ HIT  → return cached answer
                    └─ MISS → Ollama (primary)
                                └─ FAIL → OpenRouter (fallback)
                                            └─► Redis (write)
                                                  └─► User
```

See [`docs/architecture/architecture-overview.md`](docs/architecture/architecture-overview.md) for full layer breakdown.

---

## Repository Structure

```text
.
├── README.md
├── docker-compose.yml
├── .env.example
├── src/
│   ├── api/
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── dependencies.py       # Shared dependency injection
│   │   └── routers/
│   │       └── query.py          # Query endpoint with routing logic
│   ├── inference/
│   │   ├── router.py             # Primary/fallback provider routing
│   │   ├── ollama_client.py      # Local inference client
│   │   └── openrouter_client.py  # Cloud inference client
│   ├── retrieval/
│   │   ├── embedder.py           # SentenceTransformer embedding wrapper
│   │   └── qdrant_client.py      # Vector store operations
│   ├── cache/
│   │   └── redis_cache.py        # Prompt-keyed response cache
│   └── models/
│       └── schemas.py            # Pydantic request/response schemas
├── scripts/
│   ├── ingest_documents.py       # Document ingestion and indexing
│   └── health_check.py           # Platform component health checks
└── docs/
    ├── architecture/
    │   ├── architecture-overview.md
    │   └── hybrid-ai-platform.mmd
    ├── adr/
    │   ├── 0001-local-first-hybrid-inference.md
    │   ├── 0002-redis-response-cache.md
    │   └── 0003-distributed-ollama-node.md
    ├── runbooks/
    │   └── local-operations.md
    └── case-study/
        └── local-first-hybrid-ai-platform.md
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for scripts)
- Ollama installed on a local node ([ollama.ai](https://ollama.ai))
- OpenRouter API key (optional, for cloud fallback)

### 1. Clone and configure

```bash
git clone https://github.com/your-username/local-first-hybrid-ai-platform.git
cd local-first-hybrid-ai-platform
cp .env.example .env
# Edit .env with your values
```

### 2. Pull a local model

```bash
ollama pull gemma2:9b
```

### 3. Start the platform

```bash
docker compose up -d
```

### 4. Ingest documents

```bash
pip install -r scripts/requirements.txt
python scripts/ingest_documents.py --input-dir ./sample-docs
```

### 5. Open the UI

Navigate to [http://localhost:3000](http://localhost:3000)

---

## Core Design Decisions

Architecture Decision Records document all major trade-offs:

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](docs/adr/0001-local-first-hybrid-inference.md) | Adopt local-first hybrid inference strategy | Accepted |
| [0002](docs/adr/0002-redis-response-cache.md) | Introduce Redis as a response cache | Accepted |
| [0003](docs/adr/0003-distributed-ollama-node.md) | Support a distributed Ollama inference node | Accepted |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | FastAPI, Python 3.11, Pydantic v2 |
| Embedding | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Vector Store | Qdrant |
| Local Inference | Ollama (Gemma 2 9B) |
| Cloud Inference | OpenRouter (abstracted provider) |
| Caching | Redis |
| UI | Open WebUI |
| Workflow Automation | n8n |
| Infrastructure | Docker Compose, Ubuntu host |

---

## Roadmap

- [ ] Complexity-based query routing (route by token estimate)
- [ ] Session memory for multi-turn conversation context
- [ ] LLMOps observability (LangSmith / Arize integration)
- [ ] RBAC for document collection access
- [ ] FinOps dashboard (token cost tracking per query)
- [ ] Streaming response support

---

## Portfolio Context

This project is an architecture portfolio artefact. It is intentionally scoped to demonstrate:

- **Hybrid inference routing** with privacy-first defaults
- **Enterprise RAG patterns** with grounded, context-constrained responses
- **Cost optimisation** through semantic caching
- **Architectural decision making** documented via ADRs
- **Operational thinking** via runbooks and deployment topology

> **Portfolio positioning:** Designed and implemented a local-first hybrid GenAI platform integrating FastAPI, Qdrant, Ollama, Redis, and OpenRouter — enabling privacy-aware enterprise document intelligence with semantic caching and resilient multi-tier inference routing.

---

## License

MIT
