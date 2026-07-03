"use client";

import { useState } from "react";
import type { InferenceProvider } from "@/lib/api";
import ArchDiagram from "@/components/ArchDiagram";
import ChatPanel from "@/components/ChatPanel";

export default function DemoPage() {
  const [activeProvider, setActiveProvider] = useState<InferenceProvider | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <div
      className="min-h-screen"
      style={{ background: "var(--paper)", color: "var(--ink)" }}
    >
      {/* Header */}
      <header
        className="border-b px-6 py-4"
        style={{ borderColor: "var(--rule)" }}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-3">
          <div>
            <div
              className="font-mono text-xs font-medium mb-1 flex items-center gap-2"
              style={{ color: "var(--accent-mid)", letterSpacing: "0.1em" }}
            >
              <span
                className="inline-block w-5 h-px"
                style={{ background: "var(--accent-mid)" }}
              />
              PORTFOLIO DEMO — ENTERPRISE GENAI ARCHITECTURE
            </div>
            <h1
              className="font-serif text-2xl leading-tight"
              style={{ color: "var(--ink)", letterSpacing: "-0.01em" }}
            >
              Local-First{" "}
              <em className="italic" style={{ color: "var(--accent)" }}>
                Hybrid AI Platform
              </em>
            </h1>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {[
              "FastAPI",
              "Qdrant / pgvector",
              "Redis",
              "OpenRouter",
              "RAG",
            ].map((tag) => (
              <span
                key={tag}
                className="font-mono text-xs px-3 py-1 rounded-full border"
                style={{
                  borderColor: "var(--rule)",
                  background: "var(--rule-light)",
                  color: "var(--ink-3)",
                }}
              >
                {tag}
              </span>
            ))}
            <a
              href="https://github.com/faiz-faruqi/local-first-hybrid-ai-platform"
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs px-3 py-1 rounded-full border transition-colors hover:opacity-80"
              style={{
                borderColor: "var(--accent-mid)",
                background: "var(--accent-light)",
                color: "var(--accent)",
              }}
            >
              GitHub →
            </a>
          </div>
        </div>
      </header>

      {/* Main layout */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">

          {/* Left: Chat */}
          <div
            className="rounded-xl border p-5 flex flex-col"
            style={{
              borderColor: "var(--rule)",
              background: "#fff",
              minHeight: "640px",
              maxHeight: "80vh",
            }}
          >
            <div className="mb-4 pb-3 border-b" style={{ borderColor: "var(--rule)" }}>
              <div
                className="font-mono text-xs mb-1"
                style={{ color: "var(--ink-4)", letterSpacing: "0.08em" }}
              >
                QUERY INTERFACE
              </div>
              <h2 className="text-base font-semibold" style={{ color: "var(--ink)" }}>
                Document Intelligence Demo
              </h2>
                <p className="text-xs mt-1" style={{ color: "var(--ink-3)", lineHeight: 1.6 }}>
                  Querying 5 synthetic vendor contracts. The flow diagram shows the path each request takes.
                </p>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
              <ChatPanel
                onResponse={setActiveProvider}
                onLoading={setIsLoading}
              />
            </div>
          </div>

          {/* Right: Architecture diagram */}
          <div className="space-y-4 sticky top-6">
            <div
              className="rounded-xl border p-5"
              style={{ borderColor: "var(--rule)", background: "#fff" }}
            >
              <div className="mb-3 pb-3 border-b" style={{ borderColor: "var(--rule)" }}>
                <div
                  className="font-mono text-xs mb-1"
                  style={{ color: "var(--ink-4)", letterSpacing: "0.08em" }}
                >
                  LIVE ARCHITECTURE
                </div>
                <h2 className="text-base font-semibold" style={{ color: "var(--ink)" }}>
                  Request Routing
                </h2>
                <p className="text-xs mt-1" style={{ color: "var(--ink-3)", lineHeight: 1.6 }}>
                  The active path highlights after each query, reflecting which provider served the request.
                </p>
              </div>
              <ArchDiagram activeProvider={activeProvider} isLoading={isLoading} />
            </div>

            {/* Request flow legend */}
            <div
              className="rounded-xl border p-5 text-xs space-y-2"
              style={{ borderColor: "var(--rule)", background: "#fff" }}
            >
              <div
                className="font-mono mb-2"
                style={{ color: "var(--ink-4)", letterSpacing: "0.08em", fontSize: "10px" }}
              >
                REQUEST FLOW
              </div>
              {[
                { step: "01", title: "Query ingested", desc: "FastAPI receives the natural language query." },
                { step: "02", title: "Semantic retrieval", desc: "Top-k chunks pulled from Qdrant / pgvector." },
                { step: "03", title: "Cache lookup", desc: "Redis checked — hit returns instantly at <10ms." },
                { step: "04", title: "Inference routing", desc: "Cache miss → OpenRouter (cloud) via mistral-7b-instruct." },
                { step: "05", title: "Cache write", desc: "Response stored in Redis before returning to user." },
              ].map(({ step, title, desc }) => (
                <div key={step} className="flex gap-3 items-start">
                  <span
                    className="font-mono text-xs flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-center leading-none"
                    style={{ background: "var(--accent)", fontSize: "10px" }}
                  >
                    {step}
                  </span>
                  <div>
                    <span className="font-semibold" style={{ color: "var(--ink-2)" }}>{title}</span>
                    <span style={{ color: "var(--ink-4)" }}> — {desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer
        className="border-t mt-12 px-6 py-6 text-center"
        style={{ borderColor: "var(--rule)" }}
      >
        <p className="font-mono text-xs" style={{ color: "var(--ink-4)" }}>
          Built by{" "}
          <a
            href="https://github.com/faiz-faruqi"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:opacity-70 transition-opacity"
            style={{ color: "var(--accent-mid)" }}
          >
            Faiz Faruqi
          </a>
          {" "}·{" "}
          <a
            href="https://github.com/faiz-faruqi/local-first-hybrid-ai-platform"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:opacity-70 transition-opacity"
            style={{ color: "var(--accent-mid)" }}
          >
            View on GitHub
          </a>
          {" "}·{" "}
          <span>Portfolio architecture project — Enterprise GenAI</span>
        </p>
      </footer>
    </div>
  );
}
