"""Synthesis Agent - combines findings into coherent sections."""

from ..core.state import ResearchState, Section
from ..core.router import router, ModelTier


SYNTHESIS_PROMPT = """You are a research synthesis expert. Create a coherent section from the research findings.

Section Title: {section_title}

Research Findings:
{findings}

Instructions:
1. Synthesize the information into a well-structured section
2. Maintain factual accuracy and cite sources where appropriate
3. Write in a clear, professional tone
4. Include relevant details but avoid redundancy
5. If information is conflicting, acknowledge different perspectives

Write the section content:"""


def synthesis_node(state: ResearchState) -> ResearchState:
    """Synthesis Agent node.

    Combines research findings into coherent report sections.

    Args:
        state: Current research state

    Returns:
        Updated state with synthesized sections
    """
    if not state.findings:
        state.add_log("ERROR", "No findings to synthesize", agent="synthesis")
        return state

    # Get model for medium tier (synthesis requires understanding and integration)
    model, config = router.get_model(ModelTier.MEDIUM)

    # Prepare findings text
    findings_text = "\n\n".join([
        f"Query: {f.query}\nSummary: {f.summary}\n"
        f"Sources: {', '.join([s.title for s in f.sources[:3]])}"
        for f in state.findings
    ])

    # Generate sections based on expected sections in plan
    sections = []
    total_cost = 0.0

    expected_sections = state.plan.expected_sections if state.plan else ["Overview", "Details", "Conclusion"]

    for i, section_title in enumerate(expected_sections):
        try:
            prompt = SYNTHESIS_PROMPT.format(
                section_title=section_title,
                findings=findings_text,
            )

            response = model.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            # Collect source URLs for this section
            source_urls = []
            for finding in state.findings:
                for source in finding.sources:
                    if source.url not in source_urls:
                        source_urls.append(source.url)

            section = Section(
                title=section_title,
                content=content,
                sources=source_urls[:5],  # Top 5 sources
                order=i,
            )
            sections.append(section)

            # Track cost
            input_tokens = router.estimate_tokens(prompt)
            output_tokens = router.estimate_tokens(content)
            cost = router.calculate_cost(config, input_tokens, output_tokens)
            total_cost += cost

            state.add_log(
                "INFO",
                f"Synthesized section {i+1}/{len(expected_sections)}: {section_title}",
                agent="synthesis",
            )

        except Exception as e:
            state.add_log(
                "ERROR",
                f"Failed to synthesize section '{section_title}': {str(e)}",
                agent="synthesis",
            )

    # Update state
    state.sections = sections
    state.cost.add_call(config.name, 0, 0, 0)
    state.cost.add_agent_cost("synthesis", total_cost)

    state.add_log(
        "INFO",
        f"Synthesis complete. Generated {len(sections)} sections",
        agent="synthesis",
    )

    return state
