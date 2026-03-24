#!/usr/bin/env python3
"""Command-line interface for Deep Research Agent."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from deep_research_agent.core.state import ResearchState
from deep_research_agent.core.graph import create_research_graph
from deep_research_agent.agents import (
    planner_node,
    researcher_node,
    synthesis_node,
    critic_node,
    writer_node,
)
from deep_research_agent.tools.storage import save_report, save_state


async def run_research(query: str, context: str = None, max_iterations: int = 3) -> ResearchState:
    """Run a research task.

    Args:
        query: Research query
        context: Additional context
        max_iterations: Maximum iterations

    Returns:
        Final research state
    """
    # Create initial state
    state = ResearchState(
        query=query,
        context=context,
        max_iterations=max_iterations,
    )

    # Create graph
    graph = create_research_graph(
        planner_node=planner_node,
        researcher_node=researcher_node,
        synthesis_node=synthesis_node,
        critic_node=critic_node,
        writer_node=writer_node,
    )

    # Run research
    print(f"🔍 Starting research: {query}")
    print(f"📋 Trace ID: {state.trace_id}")
    print("-" * 50)

    final_state = None
    async for event in graph.astream(state, stream_mode="values"):
        final_state = event
        # Print progress
        if hasattr(event, 'iteration'):
            print(f"🔄 Iteration: {event.iteration}")
        if hasattr(event, 'plan') and event.plan:
            print(f"📊 Plan: {len(event.plan.sub_queries)} sub-queries")
        if hasattr(event, 'findings'):
            print(f"📚 Findings: {len(event.findings)} items, {len(event.sources)} unique sources")
        if hasattr(event, 'sections'):
            print(f"📝 Sections: {len(event.sections)}")
        if hasattr(event, 'review') and event.review:
            status = "✅" if event.review.status.value == "passed" else "❌"
            print(f"{status} Review: {event.review.score:.2f} - {event.review.status.value}")

    print("-" * 50)

    if final_state and final_state.report:
        print(f"✅ Research complete!")
        print(f"💰 Total cost: ${final_state.cost.total_cost_usd:.4f}")

        # Save outputs
        report_path = save_report(final_state)
        state_path = save_state(final_state)

        print(f"📄 Report saved: {report_path}")
        print(f"💾 State saved: {state_path}")
    else:
        print("❌ Research failed to produce a report")

    return final_state


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Deep Research Agent - Multi-agent deep research system"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Research query (if not provided, will prompt)",
    )
    parser.add_argument(
        "--context",
        "-c",
        help="Additional context for the research",
    )
    parser.add_argument(
        "--max-iterations",
        "-i",
        type=int,
        default=3,
        help="Maximum iterations for feedback loop (default: 3)",
    )
    parser.add_argument(
        "--batch",
        "-b",
        help="Path to file containing multiple queries (one per line)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory (default: ./output)",
    )

    args = parser.parse_args()

    # Handle batch mode
    if args.batch:
        with open(args.batch, "r") as f:
            queries = [line.strip() for line in f if line.strip()]

        print(f"🚀 Batch mode: {len(queries)} queries")

        for i, query in enumerate(queries, 1):
            print(f"\n{'=' * 60}")
            print(f"Query {i}/{len(queries)}: {query}")
            print("=" * 60)
            asyncio.run(run_research(query, args.context, args.max_iterations))

        return

    # Single query mode
    if not args.query:
        args.query = input("Enter research query: ")

    if not args.query:
        print("Error: No query provided")
        sys.exit(1)

    asyncio.run(run_research(args.query, args.context, args.max_iterations))


if __name__ == "__main__":
    main()
