# ADR 0002: Introduce Redis as a Response Cache

- **Status:** Accepted
- **Date:** 2026-04-07

## Context

Repeated queries over the same retrieved context can trigger redundant model calls. This increases latency and, in cloud paths, unnecessary API consumption.

## Decision

Introduce Redis as a response cache for LLM outputs, keyed by the grounded prompt.

## Rationale

Redis is lightweight, easy to operationalize in Docker, and well suited for low-latency key-value access patterns.

## Consequences

### Positive
- Faster repeated responses
- Lower cloud inference cost on repeated prompts
- Demonstrates an enterprise-grade optimization pattern

### Negative
- Cache invalidation must be considered when retrieval logic changes
- Cached outputs can become stale if documents are updated without cache refresh

## Alternatives considered

### No cache
Rejected because the platform would repeatedly pay the latency and cost of equivalent prompts.

### Persist answers in Postgres
Rejected because the use case is low-latency ephemeral caching, not durable transactional storage.
