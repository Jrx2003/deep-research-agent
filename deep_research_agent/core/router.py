"""Model router for intelligent LLM selection."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
import functools
import time

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from .config import settings


class ModelTier(str, Enum):
    """Model capability tiers."""

    LIGHT = "light"      # Fast, cheap - for simple tasks
    MEDIUM = "medium"    # Balanced - for most tasks
    STRONG = "strong"    # Powerful - for complex reasoning


@dataclass
class ModelConfig:
    """Configuration for a model."""

    name: str
    provider: str
    input_cost_per_1k: float  # USD
    output_cost_per_1k: float  # USD
    max_tokens: int
    supports_streaming: bool = True


# Model pricing (approximate, update as needed)
MODELS: dict[str, ModelConfig] = {
    # OpenAI models
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        provider="openai",
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        max_tokens=128000,
    ),
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        provider="openai",
        input_cost_per_1k=0.0025,
        output_cost_per_1k=0.01,
        max_tokens=128000,
    ),
    "o1-preview": ModelConfig(
        name="o1-preview",
        provider="openai",
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.06,
        max_tokens=128000,
        supports_streaming=False,
    ),
    "o1-mini": ModelConfig(
        name="o1-mini",
        provider="openai",
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.012,
        max_tokens=128000,
        supports_streaming=False,
    ),
    # Kimi (Moonshot) models - OpenAI compatible
    "moonshot-v1-8k": ModelConfig(
        name="moonshot-v1-8k",
        provider="openai",
        input_cost_per_1k=0.012,
        output_cost_per_1k=0.012,
        max_tokens=8000,
    ),
    "moonshot-v1-32k": ModelConfig(
        name="moonshot-v1-32k",
        provider="openai",
        input_cost_per_1k=0.024,
        output_cost_per_1k=0.024,
        max_tokens=32000,
    ),
    "moonshot-v1-128k": ModelConfig(
        name="moonshot-v1-128k",
        provider="openai",
        input_cost_per_1k=0.060,
        output_cost_per_1k=0.060,
        max_tokens=128000,
    ),
    # Anthropic models
    "claude-3-haiku-20240307": ModelConfig(
        name="claude-3-haiku-20240307",
        provider="anthropic",
        input_cost_per_1k=0.00025,
        output_cost_per_1k=0.00125,
        max_tokens=200000,
    ),
    "claude-3-sonnet-20241022": ModelConfig(
        name="claude-3-sonnet-20241022",
        provider="anthropic",
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        max_tokens=200000,
    ),
    "claude-3-opus-20240229": ModelConfig(
        name="claude-3-opus-20240229",
        provider="anthropic",
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.075,
        max_tokens=200000,
    ),
}


TIER_MODELS: dict[ModelTier, list[str]] = {
    ModelTier.LIGHT: [settings.model_tier_light, settings.model_fallback_light],
    ModelTier.MEDIUM: [settings.model_tier_medium, settings.model_fallback_medium],
    ModelTier.STRONG: [settings.model_tier_strong, settings.model_fallback_strong],
}


class ModelRouter:
    """Router for selecting and managing LLM models."""

    def __init__(self):
        """Initialize the model router."""
        self._models: dict[str, BaseChatModel] = {}
        self._rate_limit_timestamps: list[float] = []
        self._rate_limit = settings.requests_per_minute

    def _get_model(self, model_name: str) -> BaseChatModel:
        """Get or create a LangChain model instance."""
        if model_name not in self._models:
            config = MODELS.get(model_name)
            if not config:
                raise ValueError(f"Unknown model: {model_name}")

            if config.provider == "openai":
                if not settings.openai_api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                kwargs = {
                    "model": model_name,
                    "api_key": settings.openai_api_key,
                    "max_tokens": 4096,
                }
                if settings.openai_base_url:
                    kwargs["base_url"] = settings.openai_base_url
                self._models[model_name] = ChatOpenAI(**kwargs)
            elif config.provider == "anthropic":
                if not settings.anthropic_api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._models[model_name] = ChatAnthropic(
                    model=model_name,
                    api_key=settings.anthropic_api_key,
                    max_tokens=4096,
                )
            else:
                raise ValueError(f"Unknown provider: {config.provider}")

        return self._models[model_name]

    def get_model(self, tier: ModelTier, prefer_fallback: bool = False) -> tuple[BaseChatModel, ModelConfig]:
        """Get a model for the specified tier.

        Args:
            tier: The capability tier required
            prefer_fallback: Whether to prefer fallback model

        Returns:
            Tuple of (LangChain model, model config)
        """
        model_names = TIER_MODELS[tier]
        if prefer_fallback and len(model_names) > 1:
            model_names = model_names[1:] + model_names[:1]

        for model_name in model_names:
            try:
                model = self._get_model(model_name)
                config = MODELS[model_name]
                return model, config
            except Exception as e:
                print(f"Failed to load model {model_name}: {e}")
                continue

        raise RuntimeError(f"No models available for tier {tier}")

    def calculate_cost(self, config: ModelConfig, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of a model call.

        Args:
            config: Model configuration
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1000) * config.input_cost_per_1k
        output_cost = (output_tokens / 1000) * config.output_cost_per_1k
        return input_cost + output_cost

    def estimate_tokens(self, text: str) -> int:
        """Roughly estimate token count (4 chars ≈ 1 token).

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = time.time()
        # Remove timestamps older than 1 minute
        self._rate_limit_timestamps = [
            t for t in self._rate_limit_timestamps if now - t < 60
        ]
        if len(self._rate_limit_timestamps) >= self._rate_limit:
            sleep_time = 60 - (now - self._rate_limit_timestamps[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        self._rate_limit_timestamps.append(now)


def with_cost_tracking(func: Callable) -> Callable:
    """Decorator to track costs in agent functions.

    The decorated function must accept a 'state' parameter with a 'cost' attribute.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # This is a placeholder - actual implementation would integrate with
        # LangSmith or token counting
        return func(*args, **kwargs)
    return wrapper


# Global router instance
router = ModelRouter()
