"use client";

import type { InferenceProvider } from "@/lib/api";

interface ResponseMetaProps {
  provider: InferenceProvider;
  cached: boolean;
  latencyMs: number;
}

const PROVIDER_CONFIG: Record<
  InferenceProvider,
  { label: string; bg: string; color: string; border: string; dot: string }
> = {
  local: {
    label: "LOCAL",
    bg: "#e6f1fb",
    color: "#185fa5",
    border: "#b5d4f4",
    dot: "#185fa5",
  },
  cloud: {
    label: "CLOUD",
    bg: "#faece7",
    color: "#993c1d",
    border: "#f5c4b3",
    dot: "#993c1d",
  },
  cache: {
    label: "CACHED",
    bg: "#e1f5ee",
    color: "#0f6e56",
    border: "#9fe1cb",
    dot: "#0f6e56",
  },
};

export default function ResponseMeta({ provider, cached, latencyMs }: ResponseMetaProps) {
  const cfg = PROVIDER_CONFIG[provider];

  return (
    <div className="flex items-center gap-3 flex-wrap mt-2">
      {/* Provider badge */}
      <span
        className="font-mono text-xs font-medium px-3 py-1 rounded-full border flex items-center gap-1.5"
        style={{ background: cfg.bg, color: cfg.color, borderColor: cfg.border }}
      >
        <span
          className="inline-block w-1.5 h-1.5 rounded-full"
          style={{ background: cfg.dot }}
        />
        {cfg.label}
      </span>

      {/* Cache pill */}
      {cached && (
        <span
          className="font-mono text-xs px-2 py-0.5 rounded border"
          style={{ background: "#e1f5ee", color: "#0f6e56", borderColor: "#9fe1cb" }}
        >
          cache hit
        </span>
      )}

      {/* Latency */}
      <span
        className="font-mono text-xs"
        style={{ color: "var(--ink-4)" }}
      >
        {latencyMs < 10 ? `<10 ms` : `${Math.round(latencyMs)} ms`}
      </span>
    </div>
  );
}
