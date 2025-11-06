"""Performance monitoring and metrics tracking module.

This module provides decorators and utilities for monitoring application performance,
tracking API calls, and calculating costs.
"""

import functools
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, DefaultDict, Dict, List, Optional, TypeVar, cast

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic function decoration
F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    function_name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    errors: int = 0
    last_called: Optional[datetime] = None

    def update(self, execution_time: float, had_error: bool = False) -> None:
        """Update metrics with new execution data."""
        self.total_calls += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.total_calls
        self.last_called = datetime.now()
        if had_error:
            self.errors += 1


@dataclass
class APIMetrics:
    """Container for API call metrics."""

    endpoint: str
    total_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    errors: int = 0
    avg_latency: float = 0.0
    total_latency: float = 0.0
    last_called: Optional[datetime] = None

    def update(
        self,
        tokens: int = 0,
        cost: float = 0.0,
        latency: float = 0.0,
        had_error: bool = False
    ) -> None:
        """Update API metrics with new call data."""
        self.total_calls += 1
        self.total_tokens += tokens
        self.total_cost += cost
        self.total_latency += latency
        self.avg_latency = self.total_latency / self.total_calls
        self.last_called = datetime.now()
        if had_error:
            self.errors += 1


class MetricsCollector:
    """Singleton class for collecting and managing metrics."""

    _instance: Optional['MetricsCollector'] = None

    def __new__(cls) -> 'MetricsCollector':
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        if self._initialized:  # type: ignore
            return

        self.performance_metrics: DefaultDict[str, PerformanceMetrics] = defaultdict(
            lambda: PerformanceMetrics(function_name="unknown")
        )
        self.api_metrics: DefaultDict[str, APIMetrics] = defaultdict(
            lambda: APIMetrics(endpoint="unknown")
        )
        self._initialized = True  # type: ignore

    def get_performance_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all performance metrics."""
        return {
            name: {
                "calls": metrics.total_calls,
                "total_time": f"{metrics.total_time:.2f}s",
                "avg_time": f"{metrics.avg_time:.3f}s",
                "min_time": f"{metrics.min_time:.3f}s",
                "max_time": f"{metrics.max_time:.3f}s",
                "errors": metrics.errors,
                "last_called": metrics.last_called.isoformat() if metrics.last_called else None,
            }
            for name, metrics in self.performance_metrics.items()
        }

    def get_api_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all API metrics."""
        return {
            endpoint: {
                "calls": metrics.total_calls,
                "total_tokens": metrics.total_tokens,
                "total_cost": f"${metrics.total_cost:.4f}",
                "avg_cost_per_call": f"${(metrics.total_cost / metrics.total_calls):.4f}",
                "avg_latency": f"{metrics.avg_latency:.3f}s",
                "errors": metrics.errors,
                "last_called": metrics.last_called.isoformat() if metrics.last_called else None,
            }
            for endpoint, metrics in self.api_metrics.items()
        }

    def log_summary(self) -> None:
        """Log a summary of all collected metrics."""
        logger.info("=" * 70)
        logger.info("PERFORMANCE METRICS SUMMARY")
        logger.info("=" * 70)

        perf_summary = self.get_performance_summary()
        if perf_summary:
            for func_name, metrics in perf_summary.items():
                logger.info(f"\n{func_name}:")
                for key, value in metrics.items():
                    logger.info(f"  {key}: {value}")
        else:
            logger.info("No performance metrics collected")

        logger.info("\n" + "=" * 70)
        logger.info("API METRICS SUMMARY")
        logger.info("=" * 70)

        api_summary = self.get_api_summary()
        if api_summary:
            for endpoint, metrics in api_summary.items():
                logger.info(f"\n{endpoint}:")
                for key, value in metrics.items():
                    logger.info(f"  {key}: {value}")

            # Calculate total costs
            total_cost = sum(m.total_cost for m in self.api_metrics.values())
            total_tokens = sum(m.total_tokens for m in self.api_metrics.values())
            total_calls = sum(m.total_calls for m in self.api_metrics.values())

            logger.info("\n" + "-" * 70)
            logger.info("TOTALS:")
            logger.info(f"  Total API Calls: {total_calls}")
            logger.info(f"  Total Tokens: {total_tokens:,}")
            logger.info(f"  Total Cost: ${total_cost:.4f}")
            if total_calls > 0:
                logger.info(f"  Avg Cost/Call: ${(total_cost / total_calls):.4f}")
        else:
            logger.info("No API metrics collected")

        logger.info("=" * 70)

    def reset(self) -> None:
        """Reset all metrics."""
        self.performance_metrics.clear()
        self.api_metrics.clear()
        logger.info("All metrics have been reset")


# Global metrics collector instance
metrics_collector = MetricsCollector()


def track_performance(func: F) -> F:
    """
    Decorator to track function performance metrics.

    Args:
        func: Function to be decorated

    Returns:
        Decorated function with performance tracking

    Example:
        @track_performance
        def my_function():
            # function code
            pass
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = f"{func.__module__}.{func.__qualname__}"
        start_time = time.perf_counter()
        had_error = False

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            had_error = True
            raise
        finally:
            execution_time = time.perf_counter() - start_time

            # Update metrics
            if func_name not in metrics_collector.performance_metrics:
                metrics_collector.performance_metrics[func_name] = PerformanceMetrics(
                    function_name=func_name
                )
            metrics_collector.performance_metrics[func_name].update(execution_time, had_error)

            # Log the execution
            status = "ERROR" if had_error else "OK"
            logger.debug(
                f"[{status}] {func_name} executed in {execution_time:.3f}s"
            )

    return cast(F, wrapper)


def track_api_call(
    endpoint: str,
    model_name: str = "gemini-2.5-flash",
    input_cost_per_1m: float = 0.075,  # Gemini 2.5 Flash pricing
    output_cost_per_1m: float = 0.30   # Gemini 2.5 Flash pricing
) -> Callable[[F], F]:
    """
    Decorator to track API call metrics including tokens and costs.

    Args:
        endpoint: Name of the API endpoint (e.g., "gemini-generate-content")
        model_name: Name of the model being used
        input_cost_per_1m: Cost per 1 million input tokens (default: Gemini 2.5 Flash)
        output_cost_per_1m: Cost per 1 million output tokens (default: Gemini 2.5 Flash)

    Returns:
        Decorator function

    Example:
        @track_api_call("gemini-generate-content", model_name="gemini-2.5-flash")
        def call_ai_model(client, prompt):
            # API call code
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            had_error = False

            try:
                result = func(*args, **kwargs)

                # Try to extract token usage from result if available
                input_tokens = 0
                output_tokens = 0

                # Handle Google Gen AI response object
                if hasattr(result, 'usage_metadata'):
                    input_tokens = getattr(result.usage_metadata, 'prompt_token_count', 0)
                    output_tokens = getattr(result.usage_metadata, 'candidates_token_count', 0)

                # Calculate costs
                total_tokens = input_tokens + output_tokens
                input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
                output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
                total_cost = input_cost + output_cost

                return result
            except Exception as e:
                had_error = True
                total_tokens = 0
                total_cost = 0.0
                raise
            finally:
                latency = time.perf_counter() - start_time

                # Update metrics
                full_endpoint = f"{endpoint}:{model_name}"
                if full_endpoint not in metrics_collector.api_metrics:
                    metrics_collector.api_metrics[full_endpoint] = APIMetrics(
                        endpoint=full_endpoint
                    )
                metrics_collector.api_metrics[full_endpoint].update(
                    tokens=total_tokens,
                    cost=total_cost,
                    latency=latency,
                    had_error=had_error
                )

                # Log the API call
                status = "ERROR" if had_error else "OK"
                logger.debug(
                    f"[{status}] API call to {full_endpoint}: "
                    f"{total_tokens} tokens, ${total_cost:.4f}, {latency:.3f}s"
                )

        return cast(F, wrapper)
    return decorator


def get_metrics_summary() -> Dict[str, Dict[str, Any]]:
    """
    Get a complete summary of all metrics.

    Returns:
        Dictionary containing performance and API metrics
    """
    return {
        "performance": metrics_collector.get_performance_summary(),
        "api": metrics_collector.get_api_summary(),
    }


def log_metrics_summary() -> None:
    """Log a summary of all collected metrics."""
    # Only log detailed metrics if explicitly enabled
    if os.getenv('SHOW_PERFORMANCE_METRICS', '').lower() in ('true', '1', 'yes'):
        metrics_collector.log_summary()


def reset_metrics() -> None:
    """Reset all collected metrics."""
    metrics_collector.reset()
