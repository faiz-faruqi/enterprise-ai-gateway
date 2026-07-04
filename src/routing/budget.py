"""
Cost budget tracker — Redis-backed daily/monthly spend accounting.

The Decision Engine consults the budget tracker before selecting a model.
If the configured budget has been exceeded, the engine downgrades to a
cheaper model tier — demonstrating FinOps / cost-aware routing.

Reuses the existing Redis connection (same instance as the response cache)
but with a separate key namespace.

Budget is configured via environment variables:
    BUDGET_DAILY_USD   — daily spend cap in USD (0 or unset = no daily cap)
    BUDGET_MONTHLY_USD — monthly spend cap in USD (0 or unset = no monthly cap)
"""

import logging
import os
from datetime import datetime, timezone

from src.cache.redis_cache import ResponseCache

logger = logging.getLogger(__name__)

BUDGET_DAILY_USD = float(os.getenv("BUDGET_DAILY_USD", "0") or "0")
BUDGET_MONTHLY_USD = float(os.getenv("BUDGET_MONTHLY_USD", "0") or "0")

BUDGET_KEY_PREFIX = "budget:spend:"


class BudgetTracker:
    """
    Tracks cumulative LLM spend in Redis, keyed by day and month.

    Usage:
        tracker = BudgetTracker(cache)
        remaining = await tracker.remaining_daily()
        await tracker.record_spend(0.0023)
    """

    def __init__(
        self,
        cache: ResponseCache,
        daily_budget: float = BUDGET_DAILY_USD,
        monthly_budget: float = BUDGET_MONTHLY_USD,
    ) -> None:
        self._client = cache._client  # reuse the underlying aioredis connection
        self._daily_budget = daily_budget
        self._monthly_budget = monthly_budget

    @staticmethod
    def _daily_key() -> str:
        return f"{BUDGET_KEY_PREFIX}daily:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    @staticmethod
    def _monthly_key() -> str:
        return f"{BUDGET_KEY_PREFIX}monthly:{datetime.now(timezone.utc).strftime('%Y-%m')}"

    async def get_daily_spend(self) -> float:
        """Return total spend for today in USD."""
        try:
            val = await self._client.get(self._daily_key())
            return float(val) if val else 0.0
        except Exception as exc:
            logger.warning("Budget daily read failed: %s", exc)
            return 0.0

    async def get_monthly_spend(self) -> float:
        """Return total spend for this month in USD."""
        try:
            val = await self._client.get(self._monthly_key())
            return float(val) if val else 0.0
        except Exception as exc:
            logger.warning("Budget monthly read failed: %s", exc)
            return 0.0

    async def remaining_daily(self) -> float | None:
        """Return remaining daily budget, or None if no daily cap is set."""
        if self._daily_budget <= 0:
            return None
        spent = await self.get_daily_spend()
        return max(0.0, self._daily_budget - spent)

    async def remaining_monthly(self) -> float | None:
        """Return remaining monthly budget, or None if no monthly cap is set."""
        if self._monthly_budget <= 0:
            return None
        spent = await self.get_monthly_spend()
        return max(0.0, self._monthly_budget - spent)

    async def is_budget_exceeded(self) -> bool:
        """Return True if any configured budget has been exceeded."""
        daily_remaining = await self.remaining_daily()
        if daily_remaining is not None and daily_remaining <= 0:
            return True
        monthly_remaining = await self.remaining_monthly()
        if monthly_remaining is not None and monthly_remaining <= 0:
            return True
        return False

    async def record_spend(self, amount_usd: float) -> None:
        """Record a spend against both daily and monthly counters."""
        if amount_usd <= 0:
            return
        try:
            await self._client.incrbyfloat(self._daily_key(), amount_usd)
            await self._client.incrbyfloat(self._monthly_key(), amount_usd)
            # Set a 35-day TTL on monthly keys for automatic cleanup.
            await self._client.expire(self._monthly_key(), 35 * 24 * 3600)
            await self._client.expire(self._daily_key(), 48 * 3600)
            logger.info("Recorded spend: $%.6f", amount_usd)
        except Exception as exc:
            logger.warning("Budget spend recording failed: %s", exc)

    @property
    def has_budget_configured(self) -> bool:
        """True if any budget cap is configured."""
        return self._daily_budget > 0 or self._monthly_budget > 0
