#!/usr/bin/env python3
"""Basic research example."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.state import ResearchState
from core.graph import create_research_graph
from agents import (
    planner_node,
    researcher_node,
    synthesis_node,
    critic_node,
    writer_node,
)


async def main():
    """Run a basic research task."""
    query = "What are the latest advances in retrieval-augmented generation (RAG) for LLMs?"

    print(f"🔍 Starting research: {query}")
    print("-" * 60)

    # Create initial state
    state = ResearchState(query=query, max_iterations=2)

    # Create graph
    graph = create_research_graph(
        planner_node=planner_node,
        researcher_node=researcher_node,
        synthesis_node=synthesis_node,
        critic_node=critic_node,
        writer_node=writer_node,
    )

    # Run research
    final_state = None
    async for event in graph.astream(state, stream_mode="values"):
        final_state = event
        print(f"\n🔄 Iteration: {event.iteration}")

        if event.plan:
            print(f"📋 Plan: {len(event.plan.sub_queries)} sub-queries")

        if event.findings:
            print(f"📚 Findings: {len(event.findings)} items")

        if event.sections:
            print(f"📝 Sections: {len(event.sections)}")

        if event.review:
            status = "✅ PASS" if event.review.status.value == "passed" else "❌ FAIL"
            print(f"🔍 Review: {status} (score: {event.review.score:.2f})")

    print("\n" + "=" * 60)

    if final_state and final_state.report:
        print("\n✅ Research Complete!")
        print(f"💰 Total Cost: ${final_state.cost.total_cost_usd:.4f}")
        print(f"📄 Report Length: {len(final_state.report)} characters")
        print("\n--- Preview ---\n")
        print(final_state.report[:1000] + "...")
    else:
        print("❌ Research failed")


if __name__ == "__main__":
    asyncio.run(main())
