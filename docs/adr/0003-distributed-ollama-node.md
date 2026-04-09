# ADR 0003: Support a Distributed Ollama Inference Node

- **Status:** Accepted
- **Date:** 2026-04-07

## Context

The primary Ubuntu host runs the control plane services: FastAPI, Qdrant, Redis, Postgres, Open WebUI, and n8n. Local LLM inference on the same host can create memory pressure on constrained hardware.

## Decision

Allow Ollama to run on a secondary Windows laptop and expose it over the local network to the Ubuntu-based FastAPI service.

## Rationale

This enables the project to demonstrate distributed architecture principles while making practical use of available hardware.

## Consequences

### Positive
- Offloads local inference from the main host
- Demonstrates separation of control plane and inference plane
- Avoids immediate hardware replacement or VPS cost

### Negative
- Requires the Windows node to be powered on for local inference
- Introduces network dependency and LAN configuration steps
- Requires a fixed or reserved IP for predictable connectivity

## Alternatives considered

### Run everything on one host
Rejected because local inference competes with the platform stack for limited RAM.

### Move the full platform to a VPS
Rejected due to recurring cost and reduced local-first privacy value.
