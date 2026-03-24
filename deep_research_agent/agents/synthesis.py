"""Synthesis Agent - combines findings into coherent sections."""

import re
import asyncio
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

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


def synthesize_single_section(
    section_title: str,
    findings_text: str,
    order: int,
    state: ResearchState,
) -> Tuple[Section, float]:
    """Synthesize a single section.

    Args:
        section_title: Title of the section
        findings_text: Text containing all findings
        order: Order index for the section
        state: Research state for logging

    Returns:
        Tuple of (Section, cost)
    """
    model, config = router.get_model(ModelTier.MEDIUM)

    try:
        clean_title = clean_section_title(section_title)

        prompt = SYNTHESIS_PROMPT.format(
            section_title=clean_title,
            findings=findings_text,
        )

        response = model.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Clean up common LLM artifacts
        content = content.strip()
        content = re.sub(r'^(Section\s*Title[:\-]?\s*[^\n]*\n*)', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^({section_title}[:\-]?\s*\n*)'.format(section_title=re.escape(clean_title)), '', content, flags=re.IGNORECASE)

        # Calculate cost
        input_tokens = router.estimate_tokens(prompt)
        output_tokens = router.estimate_tokens(content)
        cost = router.calculate_cost(config, input_tokens, output_tokens)

        # Collect sources from all findings
        source_urls = []
        for finding in state.findings:
            for source in finding.sources:
                if source.url and source.url not in source_urls:
                    source_urls.append(source.url)

        section = Section(
            title=clean_title,
            content=content,
            sources=source_urls[:5],
            order=order,
        )

        return section, cost

    except Exception as e:
        # Return empty section on error
        state.add_log(
            "ERROR",
            f"Failed to synthesize section '{section_title}': {str(e)}",
            agent="synthesis",
        )
        return Section(
            title=clean_section_title(section_title),
            content="Error generating content.",
            sources=[],
            order=order,
        ), 0.0


def synthesis_node(state: ResearchState) -> ResearchState:
    """Synthesis Agent node - Parallel version.

    Combines research findings into coherent report sections in parallel.

    Args:
        state: Current research state

    Returns:
        Updated state with synthesized sections
    """
    if not state.findings:
        state.add_log("ERROR", "No findings to synthesize", agent="synthesis")
        return state

    # Prepare findings text once
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

    state.add_log(
        "INFO",
        f"Starting parallel synthesis of {len(expected_sections)} sections",
        agent="synthesis",
    )

    # Parallel synthesis using ThreadPoolExecutor
    sections = []
    total_cost = 0.0

    with ThreadPoolExecutor(max_workers=min(len(expected_sections), 4)) as executor:
        futures = {
            executor.submit(
                synthesize_single_section,
                title,
                findings_text,
                i,
                state
            ): i
            for i, title in enumerate(expected_sections)
        }

        for future in futures:
            section, cost = future.result()
            if section.content and section.content != "Error generating content.":
                sections.append(section)
                total_cost += cost
                state.add_log(
                    "INFO",
                    f"Synthesized section: {section.title}",
                    agent="synthesis",
                )

    # Sort sections by order
    sections.sort(key=lambda x: x.order)

    # Deduplication: Check for similar content
    unique_sections = []
    seen_contents = []
    for section in sections:
        is_duplicate = False
        content_start = section.content[:100].lower() if section.content else ""
        for seen in seen_contents:
            if content_start and content_start == seen:
                is_duplicate = True
                state.add_log(
                    "WARNING",
                    f"Skipping duplicate section: {section.title}",
                    agent="synthesis",
                )
                break
        if not is_duplicate:
            unique_sections.append(section)
            seen_contents.append(content_start)

    # Update state
    state.sections = unique_sections
    state.cost.add_call("parallel_synthesis", 0, 0, 0)
    state.cost.add_agent_cost("synthesis", total_cost)

    state.add_log(
        "INFO",
        f"Synthesis complete. Generated {len(unique_sections)} unique sections",
        agent="synthesis",
    )

    return state
