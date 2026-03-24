"""LangGraph workflow definition for Deep Research Agent."""

from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ResearchState, ReviewStatus


def create_research_graph(
    planner_node,
    researcher_node,
    synthesis_node,
    critic_node,
    writer_node,
) -> StateGraph:
    """Create the research workflow graph.

    Args:
        planner_node: Function for Planner Agent
        researcher_node: Function for Researcher Agent
        synthesis_node: Function for Synthesis Agent
        critic_node: Function for Critic Agent
        writer_node: Function for Writer Agent

    Returns:
        Compiled StateGraph
    """
    # Define the state graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("writer", writer_node)

    # Define edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "synthesis")
    workflow.add_edge("synthesis", "critic")

    # Conditional edge from critic
    def should_continue(state: ResearchState) -> Literal["writer", "planner"]:
        """Determine whether to continue iteration or finish."""
        if not state.review:
            return "writer"

        # If passed or max iterations reached, go to writer
        if state.review.status == ReviewStatus.PASSED:
            return "writer"

        if state.iteration >= state.max_iterations:
            return "writer"

        # Otherwise, loop back to planner for another iteration
        return "planner"

    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "writer": "writer",
            "planner": "planner",
        },
    )

    workflow.add_edge("writer", END)

    # Add checkpointing for persistence
    checkpointer = MemorySaver()

    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)

    return app


def visualize_graph(graph: StateGraph) -> str:
    """Generate Mermaid diagram of the graph.

    Args:
        graph: The compiled graph

    Returns:
        Mermaid diagram string
    """
    mermaid = """
    flowchart TD
        START([START]) --> PLANNER[Planner Agent]
        PLANNER --> RESEARCHER[Researcher Agent]
        RESEARCHER --> SYNTHESIS[Synthesis Agent]
        SYNTHESIS --> CRITIC[Critic Agent]

        CRITIC -->|Passed| WRITER[Writer Agent]
        CRITIC -->|Failed| PLANNER
        CRITIC -->|Max Iterations| WRITER

        WRITER --> END([END])

        style START fill:#90EE90
        style END fill:#FFB6C1
        style PLANNER fill:#87CEEB
        style RESEARCHER fill:#87CEEB
        style SYNTHESIS fill:#87CEEB
        style CRITIC fill:#FFD700
        style WRITER fill:#DDA0DD
    """
    return mermaid.strip()
