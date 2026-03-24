"""Planner Agent - breaks down research queries into sub-queries."""

import json

from deep_research_agent.core.state import ResearchState, ResearchPlan
from deep_research_agent.core.router import router, ModelTier


PLANNER_PROMPT = """You are a research planning expert. Your task is to break down a research query into a structured plan.

Given the research query, create:
1. A strategy for approaching the research
2. A list of specific sub-queries to investigate
3. Expected sections for the final report

Respond in JSON format:
{{
    "strategy": "Brief description of research approach",
    "sub_queries": ["query 1", "query 2", ...],
    "expected_sections": ["section 1", "section 2", ...],
    "reasoning": "Brief explanation of your planning decisions"
}}

Research Query: {query}

{context_section}

{feedback_section}
"""


def planner_node(state: ResearchState) -> ResearchState:
    """Planner Agent node.

    Breaks down the research query into a structured plan with sub-queries.

    Args:
        state: Current research state

    Returns:
        Updated state with research plan
    """
    # Increment iteration if this is a feedback loop
    if state.review and state.review.status.value == "failed":
        state.iteration += 1

    # Build context section
    context_section = ""
    if state.context:
        context_section = f"Additional Context: {state.context}"

    # Build feedback section if this is a revision
    feedback_section = ""
    if state.review and state.review.feedback:
        feedback_items = "\n".join([
            f"- {f.dimension}: {f.issue} (Suggestion: {f.suggestion})"
            for f in state.review.feedback
        ])
        feedback_section = f"""
Previous review feedback (address these issues):
{feedback_items}
"""

    # Get model for medium tier (planning requires reasoning)
    model, config = router.get_model(ModelTier.MEDIUM)

    # Build prompt
    prompt = PLANNER_PROMPT.format(
        query=state.query,
        context_section=context_section,
        feedback_section=feedback_section,
    )

    # Call LLM
    try:
        response = model.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Parse JSON response
        # Handle potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        plan_data = json.loads(content)

        # Create research plan
        state.plan = ResearchPlan(
            strategy=plan_data.get("strategy", ""),
            sub_queries=plan_data.get("sub_queries", []),
            expected_sections=plan_data.get("expected_sections", []),
            reasoning=plan_data.get("reasoning", ""),
        )

        # Log
        state.add_log(
            "INFO",
            f"Created plan with {len(state.plan.sub_queries)} sub-queries",
            agent="planner",
            strategy=state.plan.strategy,
        )

        # Estimate and track cost
        input_tokens = router.estimate_tokens(prompt)
        output_tokens = router.estimate_tokens(content)
        cost = router.calculate_cost(config, input_tokens, output_tokens)
        state.cost.add_call(config.name, input_tokens, output_tokens, cost)
        state.cost.add_agent_cost("planner", cost)

    except Exception as e:
        state.add_log("ERROR", f"Planner failed: {str(e)}", agent="planner")
        # Create a minimal fallback plan
        state.plan = ResearchPlan(
            strategy="Direct research approach",
            sub_queries=[state.query],
            expected_sections=["Overview", "Details", "Conclusion"],
            reasoning="Fallback due to planning error",
        )

    return state
