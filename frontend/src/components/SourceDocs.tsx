"use client";

import { useState } from "react";
import type { SourceDocument } from "@/lib/api";

interface SourceDocsProps {
  sources: SourceDocument[];
}

export default function SourceDocs({ sources }: SourceDocsProps) {
  const [open, setOpen] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 font-mono text-xs transition-colors"
        style={{ color: "var(--ink-3)" }}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className={`transition-transform duration-200 ${open ? "rotate-90" : ""}`}
        >
          <path d="M4 2L8 6L4 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {sources.length} source{sources.length !== 1 ? "s" : ""} retrieved
      </button>

      {open && (
        <div className="mt-2 flex flex-col gap-2">
          {sources.map((s) => (
            <div
              key={s.chunk_id}
              className="rounded-lg p-3 border text-xs"
              style={{ background: "var(--rule-light)", borderColor: "var(--rule)" }}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono font-medium" style={{ color: "var(--ink-2)" }}>
                  {s.document_name}
                </span>
                <span
                  className="font-mono text-xs px-2 py-0.5 rounded"
                  style={{ background: "var(--accent-light)", color: "var(--accent-mid)" }}
                >
                  {(s.relevance_score * 100).toFixed(1)}% match
                </span>
              </div>
              <p style={{ color: "var(--ink-3)", lineHeight: 1.6 }}>
                {s.content_preview}
                {s.content_preview.length >= 300 ? "…" : ""}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
