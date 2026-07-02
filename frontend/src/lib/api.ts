/**
 * Typed API client for the FastAPI backend.
 * Uses NEXT_PUBLIC_API_URL environment variable.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type InferenceProvider = "local" | "cloud" | "cache";

export interface SourceDocument {
  chunk_id: string;
  document_name: string;
  content_preview: string;
  relevance_score: number;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  force_cloud?: boolean;
}

export interface QueryResponse {
  answer: string;
  provider: InferenceProvider;
  cached: boolean;
  sources: SourceDocument[];
  latency_ms: number;
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
