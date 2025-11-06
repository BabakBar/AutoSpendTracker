"""Rate limiting module for API cost control.

This module provides rate limiting functionality to control API call frequency
and manage costs effectively.
"""

import functools
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Deque, Optional, TypeVar, cast

from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

# Type variable for generic function decoration
F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class RateLimitStats:
    """Statistics for rate-limited endpoints."""

    endpoint: str
    max_calls: int
    period: int  # in seconds
    current_calls: int = 0
    throttled_count: int = 0
    total_wait_time: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)

    def reset(self) -> None:
        """Reset the rate limit counter."""
        self.current_calls = 0
        self.last_reset = datetime.now()


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with sliding window algorithm.

    This implementation provides fine-grained control over API call rates
    and automatically adjusts based on error responses.
    """

    def __init__(self, max_calls: int, period: int) -> None:
        """
        Initialize the rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in the period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: Deque[float] = deque()
        self.lock = Lock()
        self.stats = RateLimitStats(
            endpoint="adaptive",
            max_calls=max_calls,
            period=period
        )

    def __call__(self, func: F) -> F:
        """Make the rate limiter work as a decorator."""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self._wait_if_needed()
            return func(*args, **kwargs)
        return cast(F, wrapper)

    def _wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        with self.lock:
            now = time.time()

            # Remove calls outside the current window
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    self.stats.throttled_count += 1
                    self.stats.total_wait_time += sleep_time
                    logger.debug(
                        f"Rate limit reached. Waiting {sleep_time:.2f}s "
                        f"({len(self.calls)}/{self.max_calls} calls in {self.period}s window)"
                    )
                    time.sleep(sleep_time)
                    # Clean up old calls after waiting
                    now = time.time()
                    while self.calls and self.calls[0] < now - self.period:
                        self.calls.popleft()

            # Record this call
            self.calls.append(now)
            self.stats.current_calls = len(self.calls)

    def get_current_usage(self) -> dict[str, Any]:
        """Get current rate limit usage."""
        with self.lock:
            now = time.time()
            # Clean up old calls
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            return {
                "current_calls": len(self.calls),
                "max_calls": self.max_calls,
                "period": self.period,
                "percentage": (len(self.calls) / self.max_calls) * 100,
                "throttled_count": self.stats.throttled_count,
                "total_wait_time": f"{self.stats.total_wait_time:.2f}s",
            }

    def reset(self) -> None:
        """Reset the rate limiter."""
        with self.lock:
            self.calls.clear()
            self.stats.reset()


# Global rate limiter instances
_rate_limiters: dict[str, AdaptiveRateLimiter] = {}
_rate_limiter_lock = Lock()


def get_rate_limiter(
    name: str,
    max_calls: int = 60,
    period: int = 60
) -> AdaptiveRateLimiter:
    """
    Get or create a rate limiter instance.

    Args:
        name: Unique name for this rate limiter
        max_calls: Maximum calls per period
        period: Period in seconds

    Returns:
        AdaptiveRateLimiter instance
    """
    with _rate_limiter_lock:
        if name not in _rate_limiters:
            _rate_limiters[name] = AdaptiveRateLimiter(max_calls, period)
            logger.debug(
                f"Created rate limiter '{name}': {max_calls} calls per {period}s"
            )
        return _rate_limiters[name]


def rate_limit(
    max_calls: int = 60,
    period: int = 60,
    name: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator for rate limiting function calls using adaptive algorithm.

    Args:
        max_calls: Maximum number of calls allowed per period
        period: Time period in seconds
        name: Optional name for the rate limiter (defaults to function name)

    Returns:
        Decorated function with rate limiting

    Example:
        @rate_limit(max_calls=10, period=60)
        def call_api():
            # API call code
            pass
    """
    def decorator(func: F) -> F:
        limiter_name = name or f"{func.__module__}.{func.__qualname__}"
        limiter = get_rate_limiter(limiter_name, max_calls, period)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            limiter._wait_if_needed()
            return func(*args, **kwargs)

        return cast(F, wrapper)
    return decorator


def simple_rate_limit(max_calls: int, period: int) -> Callable[[F], F]:
    """
    Simple rate limiting decorator using the ratelimit library.

    This is a straightforward implementation for basic rate limiting needs.

    Args:
        max_calls: Maximum number of calls allowed per period
        period: Time period in seconds

    Returns:
        Decorated function with rate limiting

    Example:
        @simple_rate_limit(max_calls=10, period=60)
        def call_api():
            # API call code
            pass
    """
    def decorator(func: F) -> F:
        # Apply both sleep_and_retry and limits decorators
        limited_func = limits(calls=max_calls, period=period)(func)
        retrying_func = sleep_and_retry(limited_func)
        return cast(F, retrying_func)
    return decorator


def get_all_rate_limiter_stats() -> dict[str, dict[str, Any]]:
    """
    Get statistics for all rate limiters.

    Returns:
        Dictionary mapping rate limiter names to their statistics
    """
    with _rate_limiter_lock:
        return {
            name: limiter.get_current_usage()
            for name, limiter in _rate_limiters.items()
        }


def log_rate_limiter_stats() -> None:
    """Log statistics for all rate limiters."""
    stats = get_all_rate_limiter_stats()

    if not stats:
        logger.info("No rate limiter statistics available")
        return

    logger.info("=" * 70)
    logger.info("RATE LIMITER STATISTICS")
    logger.info("=" * 70)

    for name, limiter_stats in stats.items():
        logger.info(f"\n{name}:")
        logger.info(f"  Current: {limiter_stats['current_calls']}/{limiter_stats['max_calls']} calls")
        logger.info(f"  Usage: {limiter_stats['percentage']:.1f}%")
        logger.info(f"  Period: {limiter_stats['period']}s")
        logger.info(f"  Throttled: {limiter_stats['throttled_count']} times")
        logger.info(f"  Total wait: {limiter_stats['total_wait_time']}")

    logger.info("=" * 70)


def reset_all_rate_limiters() -> None:
    """Reset all rate limiters."""
    with _rate_limiter_lock:
        for limiter in _rate_limiters.values():
            limiter.reset()
        logger.info("All rate limiters have been reset")


# Budget tracking for cost control
@dataclass
class CostBudget:
    """Budget tracker for API costs."""

    daily_budget: float
    current_spend: float = 0.0
    alert_threshold: float = 0.8  # Alert at 80% of budget
    budget_exceeded: bool = False

    def add_cost(self, cost: float) -> bool:
        """
        Add cost to current spend and check budget.

        Args:
            cost: Cost to add

        Returns:
            True if within budget, False if exceeded
        """
        self.current_spend += cost

        if self.current_spend >= self.daily_budget:
            self.budget_exceeded = True
            logger.error(
                f"Budget EXCEEDED! Current: ${self.current_spend:.4f}, "
                f"Budget: ${self.daily_budget:.4f}"
            )
            return False

        if self.current_spend >= (self.daily_budget * self.alert_threshold):
            logger.warning(
                f"Budget alert! Current: ${self.current_spend:.4f} "
                f"({(self.current_spend / self.daily_budget) * 100:.1f}% of ${self.daily_budget:.4f})"
            )

        return True

    def get_remaining(self) -> float:
        """Get remaining budget."""
        return max(0, self.daily_budget - self.current_spend)

    def reset(self) -> None:
        """Reset the budget tracker."""
        self.current_spend = 0.0
        self.budget_exceeded = False


# Global budget tracker
_budget_tracker: Optional[CostBudget] = None


def set_daily_budget(budget: float, alert_threshold: float = 0.8) -> CostBudget:
    """
    Set daily API cost budget.

    Args:
        budget: Daily budget in dollars
        alert_threshold: Threshold for alerts (0.0 to 1.0)

    Returns:
        CostBudget instance
    """
    global _budget_tracker
    _budget_tracker = CostBudget(daily_budget=budget, alert_threshold=alert_threshold)
    logger.info(f"Daily budget set to ${budget:.2f} (alert at {alert_threshold * 100:.0f}%)")
    return _budget_tracker


def get_budget_tracker() -> Optional[CostBudget]:
    """Get the current budget tracker."""
    return _budget_tracker


def check_budget(cost: float) -> bool:
    """
    Check if cost is within budget.

    Args:
        cost: Cost to check

    Returns:
        True if within budget, False otherwise
    """
    if _budget_tracker is None:
        return True
    return _budget_tracker.add_cost(cost)
