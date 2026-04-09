# ADR 0001: Adopt a Local-First Hybrid Inference Strategy

- **Status:** Accepted
- **Date:** 2026-04-07

## Context

The platform answers questions over enterprise documents. Some document types may contain sensitive commercial or operational information. At the same time, local models on commodity hardware may not always provide the best quality or reliability for every query type.

## Decision

Adopt a **local-first hybrid inference strategy**:

- Use Ollama-hosted local models as the default path for suitable requests.
- Use OpenRouter as a cloud fallback when local inference is unavailable or insufficient.

## Rationale

This approach balances:

- privacy and control via local inference
- response quality and resilience via cloud fallback
- practical operability on developer-grade hardware

## Consequences

### Positive
- Supports privacy-aware enterprise use cases
- Reduces dependency on cloud-only LLM access
- Creates a stronger architectural story than a single-provider integration

### Negative
- Increases operational complexity
- Requires management of local model lifecycle and node availability
- Introduces provider-routing logic

## Alternatives considered

### Cloud-only inference
Rejected because it weakens the privacy posture and limits the architectural differentiation of the platform.

### Local-only inference
Rejected because small local models on constrained hardware may not meet quality expectations for all enterprise prompts.
