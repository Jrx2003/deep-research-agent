"""Synthesis Agent - combines findings into coherent sections."""

import re
from deep_research_agent.core.state import ResearchState, Section
from deep_research_agent.core.router import router, ModelTier


SYNTHESIS_PROMPT = """You are a research synthesis expert. Create a coherent section from the research findings.

Section Topic: {section_title}

Research Findings:
{findings}

Instructions:
1. Write a comprehensive section about "{section_title}" based on the findings
2. Do NOT include "Section Title:" or any prefix in your response - start directly with the content
3. Maintain factual accuracy and cite sources naturally in the text (e.g., "According to [source]...")
4. Write in a clear, professional tone
5. Avoid repeating information that has been covered in other sections
6. Focus on insights and analysis, not just summarizing the raw findings
7. If information is conflicting, acknowledge different perspectives

Write the section content (no title, no prefix, start directly with the text):"""


def clean_section_title(title: str) -> str:
    """Clean section title by removing numeric prefixes.

    Args:
        title: Raw section title

    Returns:
        Cleaned title
    """
    # Remove patterns like "1. ", "1.1 ", "Section 1: ", etc.
    cleaned = re.sub(r'^\d+[.\d]*\s*[.:\-]?\s*', '', title)
    cleaned = re.sub(r'^section\s*\d*[:\-]?\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


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

    # Get model for medium tier
    model, config = router.get_model(ModelTier.MEDIUM)

    # Prepare findings text
    findings_text = "\n\n".join([
        f"Query: {f.query}\nSummary: {f.summary}\n"
        f"Sources: {', '.join([s.title for s in f.sources[:3]])}"
        for f in state.findings
    ])

    # Get expected sections from plan, with limits
    max_sections = 5
    if state.plan and state.plan.expected_sections:
        expected_sections = state.plan.expected_sections[:max_sections]
    else:
        expected_sections = ["Overview", "Key Findings", "Conclusion"]

    sections = []
    total_cost = 0.0
    generated_contents = []  # Track to avoid duplication

    for i, section_title in enumerate(expected_sections):
        try:
            # Clean the title
            clean_title = clean_section_title(section_title)

            prompt = SYNTHESIS_PROMPT.format(
                section_title=clean_title,
                findings=findings_text,
            )

            response = model.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            # Clean up common LLM artifacts
            content = content.strip()
            # Remove "Section Title:" or similar prefixes if LLM added them
            content = re.sub(r'^(Section\s*Title[:\-]?\s*[^\n]*\n*)', '', content, flags=re.IGNORECASE)
            content = re.sub(r'^({section_title}[:\-]?\s*\n*)'.format(section_title=re.escape(clean_title)), '', content, flags=re.IGNORECASE)

            # Check for similarity with previous sections
            is_duplicate = False
            for prev_content in generated_contents:
                # Simple similarity check - if first 100 chars are very similar
                if len(content) > 100 and len(prev_content) > 100:
                    if content[:100].lower() == prev_content[:100].lower():
                        is_duplicate = True
                        state.add_log(
                            "WARNING",
                            f"Section '{clean_title}' appears to duplicate previous content",
                            agent="synthesis",
                        )
                        break

            if is_duplicate:
                continue

            generated_contents.append(content)

            # Collect unique sources
            source_urls = []
            for finding in state.findings:
                for source in finding.sources:
                    if source.url and source.url not in source_urls:
                        source_urls.append(source.url)

            section = Section(
                title=clean_title,
                content=content,
                sources=source_urls[:5],
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
                f"Synthesized section {i+1}/{len(expected_sections)}: {clean_title}",
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
