/**
 * Typed API client for the FastAPI backend.
 * Uses NEXT_PUBLIC_API_URL environment variable.
 */

const rawApiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_BASE = rawApiBase.endsWith("/") ? rawApiBase.slice(0, -1) : rawApiBase;

export type InferenceProvider = "local" | "cloud" | "cache";

export interface SourceDocument {
  chunk_id: string;
  document_name: string;
  content_preview: string;
  relevance_score: number;
}

// ── Phase 2: Query classification ───────────────────────────────────────────

export type Complexity = "low" | "medium" | "high";
export type Domain = "general" | "finance" | "healthcare" | "legal" | "coding" | "enterprise";
export type Sensitivity = "public" | "internal" | "confidential";
export type ContextSize = "small" | "medium" | "large";
export type LatencyTier = "interactive" | "batch";

export interface QueryProfile {
  complexity: Complexity;
  domain: Domain;
  sensitivity: Sensitivity;
  context_size: ContextSize;
  rag_needed: boolean;
  latency_tier: LatencyTier;
  confidence: number;
  token_estimate: number;
  signals: string[];
}

// ── Phase 3: Routing decision ───────────────────────────────────────────────

export interface RoutingDecision {
  selected_model: string;
  selected_tier: string;
  reason: string;
  fallback_chain: string[];
  estimated_cost: number;
  budget_remaining: number | null;
  rules_matched: string[];
}

// ── Phase 1: Model catalog ──────────────────────────────────────────────────

export interface ModelInfo {
  alias: string;
  vendor: string;
  model_id: string;
  tier: string;
  context_window: number;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  latency_tier: string;
  is_local: boolean;
  description: string;
}

// ── Request / Response ──────────────────────────────────────────────────────

export interface QueryRequest {
  query: string;
  top_k?: number;
  force_cloud?: boolean;
  model?: string | null;
}

export interface QueryResponse {
  answer: string;
  provider: InferenceProvider;
  cached: boolean;
  sources: SourceDocument[];
  latency_ms: number;
  model_alias?: string | null;
  classification?: QueryProfile | null;
  routing_decision?: RoutingDecision | null;
}

export interface HealthResponse {
  status: string;
  version: string;
  demo_mode: boolean;
  vector_store: string;
  components: Record<string, string>;
}

export async function queryDocuments(req: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }

  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: HTTP ${res.status}`);
  return res.json();
}

export async function getModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_BASE}/models/`);
  if (!res.ok) throw new Error(`Failed to fetch models: HTTP ${res.status}`);
  return res.json();
}
