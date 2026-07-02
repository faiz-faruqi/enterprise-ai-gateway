"use client";

import { useEffect, useState } from "react";
import type { InferenceProvider } from "@/lib/api";

interface ArchDiagramProps {
  activeProvider: InferenceProvider | null;
  isLoading: boolean;
}

type HighlightState = {
  user: boolean;
  fastapi: boolean;
  qdrant: boolean;
  redis: boolean;
  ollama: boolean;
  openrouter: boolean;
  response: boolean;
};

const OFF: HighlightState = {
  user: false,
  fastapi: false,
  qdrant: false,
  redis: false,
  ollama: false,
  openrouter: false,
  response: false,
};

export default function ArchDiagram({ activeProvider, isLoading }: ArchDiagramProps) {
  const [hl, setHl] = useState<HighlightState>(OFF);

  useEffect(() => {
    if (isLoading) {
      // Animate through: user → fastapi → qdrant → redis
      setHl({ ...OFF, user: true, fastapi: true });
      const t1 = setTimeout(() => setHl({ ...OFF, fastapi: true, qdrant: true }), 600);
      const t2 = setTimeout(() => setHl({ ...OFF, fastapi: true, redis: true }), 1200);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
      };
    }

    if (activeProvider === null) {
      setHl(OFF);
      return;
    }

    if (activeProvider === "cache") {
      setHl({ ...OFF, redis: true, response: true });
    } else if (activeProvider === "local") {
      setHl({ ...OFF, fastapi: true, ollama: true, response: true });
    } else if (activeProvider === "cloud") {
      setHl({ ...OFF, fastapi: true, openrouter: true, response: true });
    }

    const timer = setTimeout(() => setHl(OFF), 3500);
    return () => clearTimeout(timer);
  }, [activeProvider, isLoading]);

  const nodeClass = (active: boolean, base: string) =>
    `transition-all duration-500 ${active ? base : "opacity-40"}`;

  return (
    <div className="w-full">
      {/* Demo mode notice */}
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

      <svg
        width="100%"
        viewBox="0 0 580 500"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full"
      >
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </marker>
        </defs>

        {/* USER */}
        <g className={nodeClass(hl.user, "opacity-100")}>
          <rect x="210" y="14" width="160" height="50" rx="8" fill="#e6f1fb" stroke="#b5d4f4" strokeWidth={hl.user ? 2 : 0.5} />
          <text fontFamily="Instrument Sans, sans-serif" fontSize="13" fontWeight="600" fill="#185fa5" x="290" y="35" textAnchor="middle" dominantBaseline="central">User</text>
          <text fontFamily="DM Mono, monospace" fontSize="11" fill="#378add" x="290" y="53" textAnchor="middle" dominantBaseline="central">Open WebUI</text>
        </g>

        {/* Arrow: User → FastAPI */}
        <line x1="290" y1="64" x2="290" y2="100" stroke="#378add" strokeWidth="1" markerEnd="url(#arr)" />

        {/* Tier label */}
        <text fontFamily="DM Mono, monospace" fontSize="9" letterSpacing="0.1em" fill="#9c9890" x="30" y="125" dominantBaseline="central">ORCHESTRATION</text>
        <line x1="30" y1="132" x2="550" y2="132" stroke="#dedad2" strokeWidth="0.5" strokeDasharray="3 3" />

        {/* FASTAPI */}
        <g className={nodeClass(hl.fastapi, "opacity-100")}>
          <rect x="160" y="100" width="260" height="58" rx="8" fill="#1d4e89" stroke="#185fa5" strokeWidth={hl.fastapi ? 2 : 0.5} />
          <text fontFamily="Instrument Sans, sans-serif" fontSize="13" fontWeight="600" fill="#fff" x="290" y="122" textAnchor="middle" dominantBaseline="central">FastAPI — Control Plane</text>
          <text fontFamily="DM Mono, monospace" fontSize="10" fill="rgba(255,255,255,0.65)" x="290" y="140" textAnchor="middle" dominantBaseline="central">Orchestration · Routing · Caching</text>
        </g>

        {/* Arrows: FastAPI → Qdrant & Redis */}
        <path d="M240 158 L240 230" fill="none" stroke="#9c9890" strokeWidth="1" markerEnd="url(#arr)" />
        <path d="M340 158 L340 230" fill="none" stroke="#9c9890" strokeWidth="1" markerEnd="url(#arr)" />

        {/* Tier label */}
        <text fontFamily="DM Mono, monospace" fontSize="9" letterSpacing="0.1em" fill="#9c9890" x="30" y="218" dominantBaseline="central">RETRIEVAL + CACHE</text>
        <line x1="30" y1="225" x2="550" y2="225" stroke="#dedad2" strokeWidth="0.5" strokeDasharray="3 3" />

        {/* QDRANT */}
        <g className={nodeClass(hl.qdrant, "opacity-100")}>
          <rect x="110" y="230" width="190" height="58" rx="8" fill="#e1f5ee" stroke="#9fe1cb" strokeWidth={hl.qdrant ? 2 : 0.5} />
          <text fontFamily="Instrument Sans, sans-serif" fontSize="13" fontWeight="600" fill="#0f6e56" x="205" y="251" textAnchor="middle" dominantBaseline="central">Qdrant / pgvector</text>
          <text fontFamily="DM Mono, monospace" fontSize="10" fill="#1d9e75" x="205" y="270" textAnchor="middle" dominantBaseline="central">Vector DB · Semantic Retrieval</text>
        </g>

        {/* REDIS */}
        <g className={nodeClass(hl.redis, "opacity-100")}>
          <rect x="280" y="230" width="190" height="58" rx="8" fill="#faeeda" stroke="#fac775" strokeWidth={hl.redis ? 2 : 0.5} />
          <text fontFamily="Instrument Sans, sans-serif" fontSize="13" fontWeight="600" fill="#854f0b" x="375" y="251" textAnchor="middle" dominantBaseline="central">Redis</text>
          <text fontFamily="DM Mono, monospace" fontSize="10" fill="#ba7517" x="375" y="270" textAnchor="middle" dominantBaseline="central">Query Cache · Cost Control</text>
        </g>

        {/* Return arrows from retrieval back to FastAPI */}
        <path d="M220 230 L220 210 L260 210 L260 158" fill="none" stroke="#dedad2" strokeWidth="0.75" strokeDasharray="3 2" markerEnd="url(#arr)" />
        <path d="M360 230 L360 210 L320 210 L320 158" fill="none" stroke="#dedad2" strokeWidth="0.75" strokeDasharray="3 2" markerEnd="url(#arr)" />

        {/* Arrows: FastAPI → inference tier */}
        <path d="M210 158 L150 158 L150 338" fill="none" stroke="#185fa5" strokeWidth="1" markerEnd="url(#arr)" />
        <path d="M370 158 L430 158 L430 338" fill="none" stroke="#993c1d" strokeWidth="1" strokeDasharray="5 3" markerEnd="url(#arr)" />

        {/* Tier label */}
        <text fontFamily="DM Mono, monospace" fontSize="9" letterSpacing="0.1em" fill="#9c9890" x="30" y="324" dominantBaseline="central">INFERENCE LAYER</text>
        <line x1="30" y1="331" x2="550" y2="331" stroke="#dedad2" strokeWidth="0.5" strokeDasharray="3 3" />

        {/* PRIMARY label */}
        <rect x="52" y="335" width="54" height="18" rx="3" fill="#e6f1fb" />
        <text fontFamily="DM Mono, monospace" fontSize="9" fill="#185fa5" x="79" y="344" textAnchor="middle" dominantBaseline="central">PRIMARY</text>

        {/* FALLBACK label */}
        <rect x="394" y="335" width="56" height="18" rx="3" fill="#faece7" />
        <text fontFamily="DM Mono, monospace" fontSize="9" fill="#993c1d" x="422" y="344" textAnchor="middle" dominantBaseline="central">FALLBACK</text>

        {/* OLLAMA */}
        <g className={nodeClass(hl.ollama, "opacity-100")}>
          <rect x="52" y="338" width="196" height="64" rx="8" fill="#e6f1fb" stroke="#b5d4f4" strokeWidth={hl.ollama ? 2.5 : 1.5} />
          <text fontFamily="Instrument Sans, sans-serif" fontSize="13" fontWeight="600" fill="#185fa5" x="150" y="360" textAnchor="middle" dominantBaseline="central">Ollama (Local)</text>
          <text fontFamily="DM Mono, monospace" fontSize="10" fill="#378add" x="150" y="380" textAnchor="middle" dominantBaseline="central">Gemma 2 · Privacy-first</text>
        </g>

        {/* OPENROUTER */}
        <g className={nodeClass(hl.openrouter, "opacity-100")}>
          <rect x="332" y="338" width="196" height="64" rx="8" fill="#faece7" stroke="#f5c4b3" strokeWidth={hl.openrouter ? 2.5 : 1.5} strokeDasharray="5 3" />
          <text fontFamily="Instrument Sans, sans-serif" fontSize="13" fontWeight="600" fill="#993c1d" x="430" y="360" textAnchor="middle" dominantBaseline="central">OpenRouter (Cloud)</text>
          <text fontFamily="DM Mono, monospace" fontSize="10" fill="#d85a30" x="430" y="380" textAnchor="middle" dominantBaseline="central">Complex Reasoning · Fallback</text>
        </g>

        {/* Response arrows */}
        <path d="M150 402 L150 460 L290 460" fill="none" stroke="#dedad2" strokeWidth="0.75" strokeDasharray="3 2" markerEnd="url(#arr)" />
        <path d="M430 402 L430 460 L290 460" fill="none" stroke="#dedad2" strokeWidth="0.75" strokeDasharray="3 2" markerEnd="url(#arr)" />

        {/* RESPONSE */}
        <g className={nodeClass(hl.response, "opacity-100")}>
          <rect x="210" y="450" width="160" height="34" rx="8" fill="#f1efe8" stroke="#d3d1c7" strokeWidth="0.5" />
          <text fontFamily="DM Mono, monospace" fontSize="10" fill="#5f5e5a" x="290" y="467" textAnchor="middle" dominantBaseline="central">Response → User</text>
        </g>

        {/* Legend */}
        <text fontFamily="DM Mono, monospace" fontSize="9" fill="#9c9890" x="30" y="493" dominantBaseline="central">Primary</text>
        <line x1="72" y1="493" x2="95" y2="493" stroke="#185fa5" strokeWidth="1" />
        <text fontFamily="DM Mono, monospace" fontSize="9" fill="#9c9890" x="102" y="493" dominantBaseline="central">Fallback</text>
        <line x1="143" y1="493" x2="166" y2="493" stroke="#993c1d" strokeWidth="1" strokeDasharray="4 2" />
        <text fontFamily="DM Mono, monospace" fontSize="9" fill="#9c9890" x="173" y="493" dominantBaseline="central">Return/Cache</text>
        <line x1="230" y1="493" x2="253" y2="493" stroke="#dedad2" strokeWidth="1" strokeDasharray="3 2" />
      </svg>
    </div>
  );
}
