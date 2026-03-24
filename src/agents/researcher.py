"""Researcher Agent - executes searches and gathers information."""

from src.core.state import ResearchState, Finding, Source
from src.core.router import router, ModelTier
from src.tools.search import search_multiple


RESEARCHER_PROMPT = """You are a research assistant. Summarize the search results for the query.

Query: {query}

Search Results:
{results}

Provide a concise summary of the key findings. Focus on factual information and important details.
Summary:"""


def researcher_node(state: ResearchState) -> ResearchState:
    """Researcher Agent node.

    Executes searches for each sub-query and gathers information.

    Args:
        state: Current research state

    Returns:
        Updated state with findings
    """
    if not state.plan:
        state.add_log("ERROR", "No research plan found", agent="researcher")
        return state

    # Get model for light tier (search is mostly tool calling)
    model, config = router.get_model(ModelTier.LIGHT)

    all_findings = []
    total_cost = 0.0

    for i, query in enumerate(state.plan.sub_queries):
        try:
            # Execute search
            search_results = search_multiple(query, num_results=5)

            if not search_results:
                state.add_log(
                    "WARNING",
                    f"No search results for query: {query}",
                    agent="researcher",
                )
                continue

            # Format results for LLM
            results_text = "\n\n".join([
                f"Source {j+1}:\nTitle: {r.get('title', 'N/A')}\nContent: {r.get('content', 'N/A')[:500]}"
                for j, r in enumerate(search_results)
            ])

            # Get summary from LLM
            prompt = RESEARCHER_PROMPT.format(query=query, results=results_text)
            response = model.invoke(prompt)
            summary = response.content if hasattr(response, 'content') else str(response)

            # Create sources
            sources = [
                Source(
                    url=r.get('url', ''),
                    title=r.get('title', ''),
                    content=r.get('content', ''),
                    relevance_score=r.get('score', 0.0),
                    query=query,
                )
                for r in search_results if r.get('url')
            ]

            # Create finding
            finding = Finding(
                query=query,
                sources=sources,
                summary=summary,
            )
            all_findings.append(finding)

            # Track cost
            input_tokens = router.estimate_tokens(prompt)
            output_tokens = router.estimate_tokens(summary)
            cost = router.calculate_cost(config, input_tokens, output_tokens,)
            total_cost += cost

            state.add_log(
                "INFO",
                f"Completed research for query {i+1}/{len(state.plan.sub_queries)}",
                agent="researcher",
                query=query,
                sources_found=len(sources),
            )

        except Exception as e:
            state.add_log(
                "ERROR",
                f"Research failed for query '{query}': {str(e)}",
                agent="researcher",
            )

    # Update state
    state.findings = all_findings
    state.sources = state.get_all_sources()

    # Update cost tracking
    state.cost.add_call(config.name, 0, 0, 0)  # Placeholder for aggregated call
    state.cost.add_agent_cost("researcher", total_cost)

    state.add_log(
        "INFO",
        f"Research phase complete. Found {len(state.sources)} unique sources",
        agent="researcher",
    )

    return state
