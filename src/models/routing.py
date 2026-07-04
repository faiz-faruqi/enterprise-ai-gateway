"""
Routing decision schema.

A `RoutingDecision` is the output of the Decision Engine — it captures
which model was selected, why, and the ordered fallback list for
resilience (used by Phase 4's Fallback Chain).
"""

from pydantic import BaseModel, Field


class RoutingDecision(BaseModel):
    """
    The Decision Engine's verdict for a single query.

    Produced by consuming a QueryProfile + cost budget state.
    """

    model_config = {"protected_namespaces": ()}

    selected_model: str = Field(
        description="The model alias chosen to handle the request."
    )
    selected_tier: str = Field(
        description="The tier of the selected model (local/cheap/standard/premium)."
    )
    reason: str = Field(
        description="Human-readable explanation of why this model was chosen."
    )
    fallback_chain: list[str] = Field(
        default_factory=list,
        description="Ordered list of model aliases to try if the selected model fails.",
    )
    estimated_cost: float = Field(
        default=0.0,
        description="Estimated cost in USD for this request (0.0 for local models).",
    )
    budget_remaining: float | None = Field(
        default=None,
        description="Remaining budget in USD after this request (None if no budget set).",
    )
    rules_matched: list[str] = Field(
        default_factory=list,
        description="The policy rules that fired for this decision.",
    )
