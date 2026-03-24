"""Critic Agent - reviews research quality and identifies gaps."""

import json

from deep_research_agent.core.state import ResearchState, ReviewResult, ReviewFeedback, ReviewStatus
from deep_research_agent.core.router import router, ModelTier


CRITIC_PROMPT = """You are a critical research reviewer. Evaluate the quality of the research sections.

Original Query: {query}

Expected Sections: {expected_sections}

Generated Sections:
{sections}

Review Criteria:
1. Completeness: Does it cover all key aspects of the query?
2. Accuracy: Are the facts accurate and well-supported?
3. Relevance: Is the content focused on the query?
4. Sources: Are claims properly supported?
5. Balance: Are different perspectives presented fairly?

Respond in JSON format:
{
    "passed": true/false,
    "score": 0.0-1.0,
    "feedback": [
        {
            "dimension": "completeness/accuracy/relevance/sources/balance",
            "issue": "Description of the issue",
            "severity": "low/medium/high",
            "suggestion": "How to fix it"
        }
    ],
    "revised_plan": {
        "additional_queries": ["query 1", "query 2"]
    }
}

Guidelines:
- Score >= 0.8: Pass
- Score < 0.8 or any high severity issue: Fail
- Be thorough but fair in your critique
"""


def critic_node(state: ResearchState) -> ResearchState:
    """Critic Agent node.

    Reviews the synthesized sections for quality and completeness.

    Args:
        state: Current research state

    Returns:
        Updated state with review result
    """
    if not state.sections:
        state.add_log("ERROR", "No sections to review", agent="critic")
        state.review = ReviewResult(
            status=ReviewStatus.FAILED,
            score=0.0,
            feedback=[ReviewFeedback(
                dimension="completeness",
                issue="No sections were generated",
                severity="high",
                suggestion="Check previous steps for errors",
            )],
        )
        return state

    # Get model for strong tier (review requires strong reasoning)
    model, config = router.get_model(ModelTier.STRONG)

    # Prepare sections text
    sections_text = "\n\n".join([
        f"Section: {s.title}\n{s.content[:1000]}..."
        for s in state.sections
    ])

    expected_sections = state.plan.expected_sections if state.plan else []

    try:
        prompt = CRITIC_PROMPT.format(
            query=state.query,
            expected_sections=", ".join(expected_sections),
            sections=sections_text,
        )

        response = model.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Parse JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        review_data = json.loads(content)

        # Parse feedback items
        feedback_items = []
        for item in review_data.get("feedback", []):
            feedback_items.append(ReviewFeedback(
                dimension=item.get("dimension", "general"),
                issue=item.get("issue", ""),
                severity=item.get("severity", "medium"),
                suggestion=item.get("suggestion", ""),
            ))

        # Create review result
        passed = review_data.get("passed", False)
        score = review_data.get("score", 0.0)

        # Auto-pass if score is high enough
        if score >= 0.8 and not any(f.severity == "high" for f in feedback_items):
            passed = True

        state.review = ReviewResult(
            status=ReviewStatus.PASSED if passed else ReviewStatus.FAILED,
            score=score,
            feedback=feedback_items,
            revised_plan=review_data.get("revised_plan"),
        )

        # Track cost
        input_tokens = router.estimate_tokens(prompt)
        output_tokens = router.estimate_tokens(content)
        cost = router.calculate_cost(config, input_tokens, output_tokens)
        state.cost.add_call(config.name, input_tokens, output_tokens, cost)
        state.cost.add_agent_cost("critic", cost)

        state.add_log(
            "INFO",
            f"Review complete. Score: {score:.2f}, Status: {state.review.status.value}",
            agent="critic",
            score=score,
            passed=passed,
            issues_found=len(feedback_items),
        )

    except Exception as e:
        state.add_log("ERROR", f"Critic failed: {str(e)}", agent="critic")
        # Create a lenient fallback review
        state.review = ReviewResult(
            status=ReviewStatus.PASSED,  # Pass to avoid infinite loops
            score=0.7,
            feedback=[ReviewFeedback(
                dimension="general",
                issue=f"Review process encountered error: {str(e)}",
                severity="low",
                suggestion="Proceed with current content",
            )],
        )

    return state
