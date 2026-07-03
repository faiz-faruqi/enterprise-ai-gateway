"use client";

import { useEffect, useState } from "react";
import type { InferenceProvider } from "@/lib/api";
import { getHealth } from "@/lib/api";

interface ArchDiagramProps {
  activeProvider: InferenceProvider | null;
  isLoading: boolean;
}

/**
 * Text-based request-flow diagram.
 *
 * The previous SVG diagram used static positioning with opacity-based
 * highlighting, which could not reflect the actual path a request took —
 * only which final provider was used. This component renders the pipeline
 * as a monospace flow line and highlights the real path per request,
 * driven by the `activeProvider` prop returned from each /query/ call.
 */
export default function ArchDiagram({ activeProvider, isLoading }: ArchDiagramProps) {
  const [demoMode, setDemoMode] = useState<boolean | null>(null);
  const [hl, setHl] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let alive = true;
    getHealth()
      .then((h) => {
        if (alive) setDemoMode(h.demo_mode);
      })
      .catch(() => {
        if (alive) setDemoMode(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (isLoading) {
      setHl({ user: true, fastapi: true, qdrant: true, redis: true });
      const t = setTimeout(
        () => setHl({ user: true, fastapi: true, qdrant: true, redis: true }),
        0,
      );
      return () => clearTimeout(t);
    }

    if (activeProvider === null) {
      setHl({});
      return;
    }

    if (activeProvider === "cache") {
      setHl({ user: true, fastapi: true, redis: true, response: true });
    } else if (activeProvider === "local") {
      setHl({ user: true, fastapi: true, qdrant: true, ollama: true, response: true });
    } else if (activeProvider === "cloud") {
      setHl({ user: true, fastapi: true, qdrant: true, openrouter: true, response: true });
    }

    const timer = setTimeout(() => setHl({}), 3500);
    return () => clearTimeout(timer);
  }, [activeProvider, isLoading]);

  const dim = (id: string) => (hl[id] ? "" : "opacity-30");
  const color = (id: string, on: string, off = "var(--ink-4)") =>
    hl[id] ? on : off;

  const lastPath = (): string => {
    if (isLoading) return "processing…";
    if (activeProvider === "cache") return "User → FastAPI → Redis (hit) → User";
    if (activeProvider === "local") return "User → FastAPI → Qdrant → Ollama → User";
    if (activeProvider === "cloud") return "User → FastAPI → Qdrant → OpenRouter → User";
    return "awaiting first query";
  };

  return (
    <div className="w-full">
      {/* Mode notice — conditional on backend demo_mode flag */}
      {demoMode === true && (
        <div
          className="rounded-r-lg px-4 py-2 mb-4 text-xs"
          style={{
            borderLeft: "3px solid var(--accent-mid)",
            background: "var(--accent-light)",
            color: "var(--accent)",
          }}
        >
          <span className="font-mono font-medium">DEMO NOTE</span>
          {" "}— Local node runs{" "}
          <code className="font-mono">mistral-7b-instruct</code> via OpenRouter.
          In production this is <code className="font-mono">gemma2:9b</code> on-premises.
        </div>
      )}
      {demoMode === false && (
        <div
          className="rounded-r-lg px-4 py-2 mb-4 text-xs"
          style={{
            borderLeft: "3px solid var(--accent)",
            background: "var(--accent-light)",
            color: "var(--accent)",
          }}
        >
          <span className="font-mono font-medium">PRODUCTION MODE</span>
          {" "}— Local-first routing active. Ollama (<code className="font-mono">gemma2:9b</code>)
          is primary; OpenRouter is fallback.
        </div>
      )}

      {/* Flow diagram */}
      <div
        className="font-mono text-xs leading-relaxed rounded-lg border p-4"
        style={{
          borderColor: "var(--rule)",
          background: "var(--rule-light)",
          color: "var(--ink-2)",
        }}
      >
        <div className={dim("user")} style={{ color: color("user", "var(--accent)") }}>
          ┌─ User
        </div>
        <div className={dim("user")} style={{ color: color("user", "var(--accent-mid)") }}>
          │  query
        </div>
        <div className={dim("fastapi")} style={{ color: color("fastapi", "var(--accent)") }}>
          ▼  FastAPI — Control Plane
        </div>
        <div className={dim("fastapi")} style={{ color: color("fastapi", "var(--accent-mid)") }}>
          │  routing · caching
        </div>
        <div className={dim("qdrant")} style={{ color: color("qdrant", "#0f6e56") }}>
          ├─▶ Qdrant / pgvector
        </div>
        <div className={dim("redis")} style={{ color: color("redis", "#854f0b") }}>
          ├─▶ Redis
        </div>
        <div className={dim("fastapi")} style={{ color: color("fastapi", "var(--accent-mid)") }}>
          │  cache miss → infer
        </div>
        <div className={dim("ollama")} style={{ color: color("ollama", "var(--accent)") }}>
          ├─▶ Ollama (local)        [PRIMARY]
        </div>
        <div className={dim("openrouter")} style={{ color: color("openrouter", "#993c1d") }}>
        └─▶ OpenRouter (cloud)     [FALLBACK]
        </div>
        <div className={dim("fastapi")} style={{ color: color("fastapi", "var(--accent-mid)") }}>
          │
        </div>
        <div className={dim("response")} style={{ color: color("response", "var(--ink-2)") }}>
          ▼  Response → User
        </div>
      </div>

      {/* Last request path */}
      <div className="mt-3 flex items-center gap-2">
        <span
          className="font-mono text-xs"
          style={{ color: "var(--ink-4)", letterSpacing: "0.08em" }}
        >
          LAST REQUEST
        </span>
        <span
          className="font-mono text-xs px-2 py-0.5 rounded border"
          style={{
            borderColor: "var(--rule)",
            background: "var(--paper)",
            color: "var(--ink-2)",
          }}
        >
          {lastPath()}
        </span>
      </div>
    </div>
  );
}
