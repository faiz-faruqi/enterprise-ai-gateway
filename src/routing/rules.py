"""
Rule-based classification heuristics for the Query Classifier.

This module contains the keyword lexicons, pattern matchers, and scoring
functions used to derive a QueryProfile from raw query text — without
any LLM call. This keeps classification fast (<1ms) and deterministic.

A future enhancement (Phase 2b) could add a small LLM-based classifier
for higher accuracy, but the rule-based version is sufficient to
demonstrate the architectural pattern.
"""

import re

from src.models.classification import (
    Complexity,
    ContextSize,
    Domain,
    LatencyTier,
    Sensitivity,
)


def _keyword_match(keyword: str, text: str) -> bool:
    """
    Match a keyword against text using word boundaries.

    Single-word keywords use \\b boundaries to avoid false positives
    (e.g. "api" matching inside "capital"). Multi-word keywords
    (containing spaces) are matched as substrings since they are
    already specific enough.
    """
    if " " in keyword:
        return keyword in text
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


# ── Domain lexicons ──────────────────────────────────────────────────────────

DOMAIN_KEYWORDS: dict[Domain, list[str]] = {
    Domain.FINANCE: [
        "revenue", "cost", "budget", "invoice", "payment", "financial",
        "p&l", "profit", "loss", "audit", "tax", "expense", "forecast",
        "valuation", "ebitda", "roi", "capex", "opex", "ledger",
    ],
    Domain.HEALTHCARE: [
        "patient", "diagnosis", "treatment", "medical", "clinical",
        "hipaa", "health", "pharmacy", "prescription", "symptom",
        "doctor", "hospital", "ehr", "diagnostic",
    ],
    Domain.LEGAL: [
        "contract", "agreement", "clause", "liability", "indemnity",
        "termination", "jurisdiction", "compliance", "regulatory",
        "litigation", "arbitration", "warranty", "confidentiality",
        "nda", "legal", "statute", "provision",
    ],
    Domain.CODING: [
        "code", "function", "api", "bug", "debug", "compile", "runtime",
        "algorithm", "database", "sql", "python", "javascript", "typescript",
        "refactor", "deploy", "docker", "kubernetes", "git", "class",
        "endpoint", "stack trace",
    ],
    Domain.ENTERPRISE: [
        "architecture", "togaf", "governance", "strategy", "roadmap",
        "stakeholder", "capability", "framework", "transformation",
        "migration", "cloud", "enterprise", "business", "process",
        "operation", "vendor", "sla", "kpi", "okr",
    ],
}

# ── Complexity indicators ────────────────────────────────────────────────────

COMPLEXITY_HIGH_PATTERNS = [
    r"\bdesign\b", r"\barchitect\b", r"\bcompare\b", r"\banalyz",
    r"\bevaluat\b", r"\bstrategy\b", r"\bplan\b", r"\bpropose\b",
    r"\bhow (do|should|would|can) we\b", r"\bstep.by.step\b",
    r"\bmulti.?cloud\b", r"\bmigrat", r"\btransform",
]
COMPLEXITY_HIGH_KEYWORDS = [
    "design", "architecture", "compare", "analyze", "evaluate", "strategy",
    "comprehensive", "detailed", "multi-step", "end-to-end",
]

COMPLEXITY_LOW_PATTERNS = [
    r"^(what|who|when|where|is|are|does|did|can)\b.{0,40}\?$",
    r"\bdefine\b", r"\blist\b",
]

# ── Sensitivity indicators ───────────────────────────────────────────────────

SENSITIVITY_CONFIDENTIAL_KEYWORDS = [
    "salary", "ssn", "social security", "credit card", "password",
    "credential", "secret", "api key", "private key", "patient record",
    "confidential", "classified", "internal only", "restricted",
    "merger", "acquisition", "layoff", "termination",
]
SENSITIVITY_INTERNAL_KEYWORDS = [
    "internal", "employee", "policy", "handbook", "org chart",
    "cio", "cto", "board", "executive", "roadmap", "okr",
]

# ── RAG-needed indicators ────────────────────────────────────────────────────

RAG_NEEDED_PATTERNS = [
    r"\bour\b", r"\bwe\b", r"\bcompany\b", r"\borganization\b",
    r"\bpolicy\b", r"\bdocument\b", r"\bcontract\b", r"\bagreement\b",
    r"\bwho is\b", r"\bwhat does.*say\b", r"\baccording to\b",
    r"\bfind\b", r"\bsearch\b", r"\bwhere is\b",
]
RAG_NOT_NEEDED_PATTERNS = [
    r"\bexplain\b", r"\bdefine\b", r"\bwhat is\b", r"\bhow does\b.{0,30}(work|function)",
    r"\btutorial\b", r"\bexample of\b",
]

# ── Batch / latency indicators ───────────────────────────────────────────────

BATCH_INDICATORS = [
    "report", "analysis", "summary", "document", "generate",
    "comprehensive", "detailed", "full", "complete",
]


def estimate_tokens(text: str) -> int:
    """
    Rough token estimate: ~4 chars per token (industry rule of thumb).

    Good enough for routing decisions; not meant for billing.
    """
    return max(1, len(text) // 4)


def classify_context_size(query: str, context_chars: int = 0) -> ContextSize:
    """Bucket the combined query + retrieved context by character length."""
    total = len(query) + context_chars
    if total < 500:
        return ContextSize.SMALL
    if total <= 2000:
        return ContextSize.MEDIUM
    return ContextSize.LARGE


def detect_domain(query: str) -> tuple[Domain, list[str]]:
    """
    Detect the query domain by keyword matching.

    Returns the domain and the list of matched signals.
    """
    query_lower = query.lower()
    scores: dict[Domain, list[str]] = {d: [] for d in Domain}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            # Use word-boundary matching to avoid false positives like
            # "api" matching inside "capital". Multi-word keywords (with
            # spaces) are matched as substrings since they're already
            # specific enough.
            if " " in kw:
                if kw in query_lower:
                    scores[domain].append(kw)
            else:
                if re.search(rf"\b{re.escape(kw)}\b", query_lower):
                    scores[domain].append(kw)

    # Pick the domain with the most keyword hits; default to general.
    best_domain = Domain.GENERAL
    best_count = 0
    for domain, hits in scores.items():
        if len(hits) > best_count:
            best_count = len(hits)
            best_domain = domain

    return best_domain, scores[best_domain]


def score_complexity(query: str) -> tuple[Complexity, list[str]]:
    """
    Score query complexity using pattern + keyword matching.

    Returns the complexity level and the signals that drove the decision.
    """
    query_lower = query.lower()
    signals: list[str] = []
    score = 0

    # High-complexity patterns
    for pattern in COMPLEXITY_HIGH_PATTERNS:
        if re.search(pattern, query_lower):
            score += 2
            signals.append(f"pattern:{pattern}")

    for kw in COMPLEXITY_HIGH_KEYWORDS:
        if kw in query_lower:
            score += 1
            signals.append(f"keyword:{kw}")

    # Low-complexity patterns (short factual questions)
    for pattern in COMPLEXITY_LOW_PATTERNS:
        if re.search(pattern, query_lower):
            score -= 1
            signals.append(f"simple:{pattern}")

    # Length-based heuristic
    token_est = estimate_tokens(query)
    if token_est > 50:
        score += 1
        signals.append(f"long_query({token_est}t)")
    elif token_est < 10:
        score -= 1
        signals.append(f"short_query({token_est}t)")

    if score >= 3:
        return Complexity.HIGH, signals
    if score >= 1:
        return Complexity.MEDIUM, signals
    return Complexity.LOW, signals


def detect_sensitivity(query: str) -> tuple[Sensitivity, list[str]]:
    """
    Detect data sensitivity for governance routing.

    Returns the sensitivity level and matched signals.
    """
    query_lower = query.lower()
    signals: list[str] = []

    for kw in SENSITIVITY_CONFIDENTIAL_KEYWORDS:
        if _keyword_match(kw, query_lower):
            signals.append(f"confidential:{kw}")

    if signals:
        return Sensitivity.CONFIDENTIAL, signals

    for kw in SENSITIVITY_INTERNAL_KEYWORDS:
        if _keyword_match(kw, query_lower):
            signals.append(f"internal:{kw}")

    if signals:
        return Sensitivity.INTERNAL, signals

    return Sensitivity.PUBLIC, signals


def detect_rag_needed(query: str) -> tuple[bool, list[str]]:
    """
    Determine whether enterprise document retrieval (RAG) is needed.

    Returns (rag_needed, signals).
    """
    query_lower = query.lower()
    signals: list[str] = []

    rag_score = 0
    for pattern in RAG_NEEDED_PATTERNS:
        if re.search(pattern, query_lower):
            rag_score += 1
            signals.append(f"rag_signal:{pattern}")

    for pattern in RAG_NOT_NEEDED_PATTERNS:
        if re.search(pattern, query_lower):
            rag_score -= 1
            signals.append(f"no_rag:{pattern}")

    return rag_score > 0, signals


def detect_latency_tier(query: str) -> tuple[LatencyTier, list[str]]:
    """
    Detect whether the query implies an interactive (fast) or batch (slow OK) response.

    Returns (latency_tier, signals).
    """
    query_lower = query.lower()
    signals: list[str] = []

    for kw in BATCH_INDICATORS:
        if _keyword_match(kw, query_lower):
            signals.append(f"batch:{kw}")

    if signals:
        return LatencyTier.BATCH, signals

    return LatencyTier.INTERACTIVE, signals


def compute_confidence(signals: list[str]) -> float:
    """
    Compute a rough classifier confidence score.

    More signals → higher confidence. Capped at 0.95 (rule-based
    classifiers are never fully certain).
    """
    return min(0.95, 0.5 + len(signals) * 0.08)
