# GitHub Upload Instructions

Complete step-by-step guide to publishing this repository on GitHub
and making it portfolio-ready.

---

## Prerequisites

- Git installed locally (`git --version`)
- A GitHub account
- GitHub CLI (optional but faster): `gh` ([cli.github.com](https://cli.github.com))

---

## Step 1 — Create the GitHub repository

### Option A: GitHub CLI (recommended)

```bash
gh repo create local-first-hybrid-ai-platform \
  --public \
  --description "Privacy-aware enterprise document intelligence: RAG + local inference + semantic caching" \
  --clone
```

### Option B: GitHub website

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `local-first-hybrid-ai-platform`
3. Description: `Privacy-aware enterprise document intelligence: RAG + local inference + semantic caching`
4. Visibility: **Public** (required for portfolio visibility)
5. Do **not** initialise with README, .gitignore, or licence (these are already included)
6. Click **Create repository**

---

## Step 2 — Initialise and push the local repository

```bash
# Navigate into the project folder
cd local-first-hybrid-ai-platform

# Initialise git (if not already done)
git init

# Stage all files
git add .

# Initial commit
git commit -m "feat: initial portfolio release — local-first hybrid AI platform"

# Add your GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/local-first-hybrid-ai-platform.git

# Push to main
git branch -M main
git push -u origin main
```

---

## Step 3 — Configure repository settings on GitHub

Go to your repository → **Settings** and apply the following:

### General
- **Description**: `Privacy-aware enterprise document intelligence: RAG + local inference + semantic caching`
- **Website**: Leave blank or add your portfolio site URL
- **Topics** (click the gear icon next to About):
  ```
  generative-ai  rag  fastapi  qdrant  ollama  redis  langchain
  enterprise-ai  llm  hybrid-inference  python  docker  portfolio
  llmops  vector-database
  ```

### Features to enable
- [x] Issues
- [x] Discussions (optional — good for engagement)
- [ ] Wikis (not needed — docs are in the repo)

---

## Step 4 — Pin the repository to your GitHub profile

1. Go to your GitHub profile page: `github.com/YOUR_USERNAME`
2. Click **Customize your pins**
3. Select `local-first-hybrid-ai-platform`
4. Click **Save pins**

This puts the project front and centre on your profile — essential for hiring managers who visit.

---

## Step 5 — Verify the repository renders correctly

Check each of the following displays as expected:

| Item | Where to check |
|------|---------------|
| README with Mermaid diagram | Repository home page |
| ADRs render cleanly | `docs/adr/` folder |
| CI badge (if added) | README top section |
| File structure matches expected layout | Repository file tree |

### Add a CI status badge to the README (recommended)

After your first CI run, add this badge to the top of `README.md`.
Replace `YOUR_USERNAME`:

```markdown
![CI](https://github.com/YOUR_USERNAME/local-first-hybrid-ai-platform/actions/workflows/ci.yml/badge.svg)
```

---

## Step 6 — Create a v0.1.0 release (recommended)

Releases signal maturity to hiring managers and make the project look production-aware.

```bash
# Tag the release
git tag -a v0.1.0 -m "Portfolio release v0.1.0 — core RAG platform with hybrid inference"
git push origin v0.1.0
```

Then on GitHub:
1. Go to **Releases** → **Create a new release**
2. Tag: `v0.1.0`
3. Title: `v0.1.0 — Local-First Hybrid AI Platform`
4. Description (paste this):

```
Initial portfolio release.

Core capabilities:
- RAG pipeline over enterprise documents (Qdrant + SentenceTransformers)
- Local-first inference with Ollama (Gemma 2 9B)
- Cloud fallback via OpenRouter
- Semantic response caching with Redis
- FastAPI orchestration layer
- Docker Compose single-command deployment
- Architecture Decision Records (ADRs) for all major design choices
```

---

## Step 7 — Link from LinkedIn and your portfolio site

### LinkedIn post announcing the project

Post this (or a variant) within 24 hours of publishing:

---

*"Just published a new architecture portfolio project on GitHub.*

*Problem: Enterprises want AI-assisted answers over sensitive internal documents — without routing data to external providers or absorbing unpredictable cloud costs.*

*Solution I built: A local-first hybrid RAG platform combining:*
*→ Ollama (local inference, privacy-first)*
*→ Qdrant (vector retrieval)*
*→ Redis (semantic response caching — 60-80% cost reduction on repeated queries)*
*→ OpenRouter (cloud fallback when needed)*
*→ FastAPI orchestration layer*

*The project includes full Architecture Decision Records (ADRs) documenting why each design choice was made — not just what was built.*

*Link in comments.*

*#GenAI #EnterpriseArchitecture #RAG #LLM #Python #PortfolioProject"*

---

### Portfolio site

If you have a personal site, add the project as a case study card with:
- Title
- Problem statement (1 sentence)
- Stack icons
- Link to GitHub
- Link to the case study doc at `docs/case-study/`

---

## Step 8 — Keep the repository active

GitHub surfaces recently-active repositories. Aim for at least one meaningful commit per week:

| Week | Suggested commit |
|------|-----------------|
| 1 | Add streaming response support to the API |
| 2 | Add complexity-based routing logic to the inference router |
| 3 | Add LangSmith tracing integration |
| 4 | Add FinOps cost-tracking middleware |

Each of these maps directly to the Roadmap in the README — work through it deliberately.

---

## Repository health checklist

Before sharing with a hiring manager, confirm all of these:

- [ ] README renders cleanly with Mermaid diagram visible
- [ ] `.env.example` present (`.env` is gitignored)
- [ ] CI workflow passing (green badge)
- [ ] ADRs present and readable in `docs/adr/`
- [ ] Case study present in `docs/case-study/`
- [ ] Topics/tags added to repository
- [ ] Repository pinned on GitHub profile
- [ ] v0.1.0 release created
- [ ] LinkedIn post published with GitHub link in comments
