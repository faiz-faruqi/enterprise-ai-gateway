# Architecture Overview

## Purpose

This platform is designed to demonstrate how enterprise document intelligence can be implemented using a hybrid AI architecture that balances:

- privacy
- response quality
- cost control
- operational resilience

## Business problem

Organizations often need to query sensitive internal documents using natural language without sending all content to a third-party model provider.

The platform addresses that requirement by:

1. indexing enterprise content into a vector store
2. retrieving relevant context for each user question
3. generating answers locally when possible
4. caching repeated responses
5. falling back to cloud inference when needed

## Architecture layers

### 1. Experience layer
- Open WebUI
- API clients
- n8n workflow triggers

### 2. Orchestration layer
- FastAPI service
- prompt assembly
- provider routing
- cache lookup

### 3. Knowledge layer
- Qdrant for vector retrieval
- embeddings generated using SentenceTransformers

### 4. Inference layer
- Ollama for local inference
- OpenRouter for cloud inference

### 5. Optimization layer
- Redis for response caching

## Request flow

1. User submits a question via Open WebUI or an API client.
2. FastAPI embeds the user query.
3. Qdrant returns the top matching document chunks.
4. FastAPI builds a grounded prompt from the retrieved context.
5. Redis is checked for a cached answer.
6. On cache miss, FastAPI calls Ollama.
7. If Ollama is unavailable or unsuitable, FastAPI falls back to OpenRouter.
8. The answer is stored in Redis.
9. The response is returned to the user with source documents.

## Design principles

### Grounded responses
Answers are constrained to retrieved context rather than unconstrained chat generation.

### Local-first inference
Sensitive workloads can remain within the local environment whenever possible.

### Graceful degradation
The platform continues to operate even if the local inference node is unavailable.

### Modularity
The vector store, cache, inference provider, and UI are replaceable components.

## Deployment considerations

### Single-node deployment
Suitable for simple demos and prototypes.

### Split-node deployment
Suitable for constrained developer laptops where local LLM inference is offloaded to a second node.

## Non-functional considerations

- **Latency:** improved by Redis response cache
- **Privacy:** improved by local inference path
- **Cost:** reduced by caching and local model usage
- **Reliability:** improved by fallback design
- **Maintainability:** improved by ADRs and modular service boundaries
