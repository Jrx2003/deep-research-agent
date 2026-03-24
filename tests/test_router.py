"""Tests for model router."""

import pytest

from deep_research_agent.core.router import ModelRouter, ModelTier, ModelConfig, MODELS


def test_model_config():
    """Test model configuration."""
    config = ModelConfig(
        name="test-model",
        provider="openai",
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03,
        max_tokens=1000,
    )

    assert config.name == "test-model"
    assert config.input_cost_per_1k == 0.01


def test_router_calculate_cost():
    """Test cost calculation."""
    router = ModelRouter()

    config = MODELS["gpt-4o-mini"]
    cost = router.calculate_cost(config, 1000, 500)

    # gpt-4o-mini: $0.00015/1K input, $0.0006/1K output
    expected = (1000 / 1000) * 0.00015 + (500 / 1000) * 0.0006
    assert cost == pytest.approx(expected, rel=1e-5)


def test_estimate_tokens():
    """Test token estimation."""
    router = ModelRouter()

    # Roughly 4 chars per token
    text = "a" * 400
    assert router.estimate_tokens(text) == 100


def test_model_tier_enum():
    """Test model tier enum."""
    assert ModelTier.LIGHT.value == "light"
    assert ModelTier.MEDIUM.value == "medium"
    assert ModelTier.STRONG.value == "strong"
