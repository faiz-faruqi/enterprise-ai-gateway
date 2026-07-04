import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Enterprise AI Gateway — Intelligent Multi-LLM Routing",
  description:
    "A policy-driven AI gateway that classifies queries and routes them to the optimal LLM based on complexity, sensitivity, cost, and latency. Built by Faiz Faruqi.",
  openGraph: {
    title: "Enterprise AI Gateway — Intelligent Multi-LLM Routing",
    description: "Intelligent multi-LLM routing platform: query classification, policy-driven model selection, cost-aware routing, and vendor-neutral inference.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
