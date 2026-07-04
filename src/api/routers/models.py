"""
Models endpoint — exposes the gateway's model catalogue.

GET /models returns the full list of routable models with their metadata
(vendor, tier, cost, context window). This lets clients discover which
models the gateway can route to and make informed explicit selections
via the `model` field on the query request.
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_provider_registry
from src.inference.provider_registry import ProviderRegistry
from src.models.schemas import ModelInfo

router = APIRouter()


@router.get("/", response_model=list[ModelInfo], tags=["Models"])
async def list_models(
    registry: ProviderRegistry = Depends(get_provider_registry),
) -> list[dict]:
    """
    List every model the gateway can route to.

    Each entry includes the alias (usable as the `model` field on a query
    request), vendor, tier, cost, context window, and a short description.
    """
    return registry.describe()
