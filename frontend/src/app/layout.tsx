import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Local-First Hybrid AI Platform — Live Demo",
  description:
    "Privacy-aware enterprise document intelligence: RAG + hybrid inference + semantic caching. Built by Faiz Faruqi.",
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
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
