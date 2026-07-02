import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Local-First Hybrid AI Platform — Live Demo",
  description:
    "Privacy-aware enterprise document intelligence: RAG + local inference + semantic caching. Built by Faiz Faruqi.",
  openGraph: {
    title: "Local-First Hybrid AI Platform",
    description: "Enterprise GenAI architecture demo: hybrid inference routing, RAG, and semantic caching.",
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
      <body>{children}</body>
    </html>
  );
}
