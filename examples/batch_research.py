#!/usr/bin/env python3
"""Batch research example."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

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


# List of research topics
TOPICS = [
    "What are the key differences between GPT-4 and Claude 3?",
    "How does vector search work in modern databases?",
    "What are the latest developments in quantum computing hardware?",
]


async def research_single(query: str, index: int, total: int) -> ResearchState:
    """Research a single topic."""
    print(f"\n{'=' * 60}")
    print(f"[{index}/{total}] {query}")
    print("=" * 60)

    state = ResearchState(query=query, max_iterations=1)

    graph = create_research_graph(
        planner_node=planner_node,
        researcher_node=researcher_node,
        synthesis_node=synthesis_node,
        critic_node=critic_node,
        writer_node=writer_node,
    )

    final_state = None
    async for event in graph.astream(state, stream_mode="values"):
        final_state = event

    if final_state:
        print(f"✅ Complete - Cost: ${final_state.cost.total_cost_usd:.4f}")

    return final_state


async def main():
    """Run batch research."""
    print(f"🚀 Batch Research - {len(TOPICS)} topics")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []
    total_cost = 0.0

    for i, topic in enumerate(TOPICS, 1):
        try:
            result = await research_single(topic, i, len(TOPICS))
            if result:
                results.append(result)
                total_cost += result.cost.total_cost_usd
        except Exception as e:
            print(f"❌ Error researching '{topic}': {e}")

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 BATCH RESEARCH SUMMARY")
    print("=" * 60)
    print(f"Total topics: {len(TOPICS)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(TOPICS) - len(results)}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Average cost per topic: ${total_cost / len(results):.4f}")


if __name__ == "__main__":
    asyncio.run(main())
