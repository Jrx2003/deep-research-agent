"""Tests for state management."""

import pytest

from deep_research_agent.core.state import (
    ResearchState,
    ResearchPlan,
    Finding,
    Section,
    ReviewResult,
    ReviewStatus,
    Source,
    CostTracker,
)


def test_research_state_creation():
    """Test creating a research state."""
    state = ResearchState(query="test query")

    assert state.query == "test query"
    assert state.trace_id is not None
    assert state.iteration == 0
    assert state.findings == []
    assert state.sections == []


def test_research_state_is_complete():
    """Test state completion check."""
    state = ResearchState(query="test")
    assert not state.is_complete()

    state.report = "Test report"
    assert state.is_complete()


def test_cost_tracker():
    """Test cost tracking."""
    tracker = CostTracker()

    tracker.add_call("gpt-4", 1000, 500, 0.03)
    assert tracker.input_tokens == 1000
    assert tracker.output_tokens == 500
    assert tracker.total_cost_usd == 0.03
    assert tracker.calls_by_model["gpt-4"] == 1

    tracker.add_agent_cost("planner", 0.01)
    assert tracker.cost_by_agent["planner"] == 0.01


def test_source_creation():
    """Test creating a source."""
    source = Source(
        url="https://example.com",
        title="Example",
        content="Test content",
        relevance_score=0.9,
    )

    assert source.url == "https://example.com"
    assert source.to_dict()["url"] == "https://example.com"


def test_research_plan():
    """Test research plan."""
    plan = ResearchPlan(
        strategy="Test strategy",
        sub_queries=["q1", "q2"],
        expected_sections=["s1", "s2"],
    )

    assert len(plan.sub_queries) == 2
    assert plan.to_dict()["strategy"] == "Test strategy"


def test_review_result():
    """Test review result."""
    review = ReviewResult(
        status=ReviewStatus.PASSED,
        score=0.85,
        feedback=[],
    )

    assert review.status == ReviewStatus.PASSED
    assert review.score == 0.85
