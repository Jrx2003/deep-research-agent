"""Streamlit UI for Deep Research Agent."""

import asyncio
from datetime import datetime

import streamlit as st

from core.state import ResearchState
from core.graph import create_research_graph, visualize_graph
from agents import (
    planner_node,
    researcher_node,
    synthesis_node,
    critic_node,
    writer_node,
)
from tools.storage import save_report


st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🔍",
    layout="wide",
)


def init_session_state():
    """Initialize session state."""
    if "research_state" not in st.session_state:
        st.session_state.research_state = None
    if "logs" not in st.session_state:
        st.session_state.logs = []


async def run_research_streaming(query: str, context: str, max_iterations: int):
    """Run research with streaming updates."""
    # Create initial state
    state = ResearchState(
        query=query,
        context=context if context else None,
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

    # Run research with streaming
    async for event in graph.astream(state, stream_mode="values"):
        st.session_state.research_state = event
        st.session_state.logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "iteration": event.iteration,
            "findings": len(event.findings),
            "sections": len(event.sections),
        })
        # Trigger rerun to update UI
        st.rerun()


def main():
    """Main UI."""
    init_session_state()

    st.title("🔍 Deep Research Agent")
    st.markdown("Multi-agent deep research system with automated planning, research, synthesis, and review.")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        max_iterations = st.slider(
            "Max Iterations",
            min_value=1,
            max_value=5,
            value=3,
            help="Maximum number of feedback loops",
        )

        st.header("📊 Architecture")
        mermaid = visualize_graph(None)
        st.markdown(f"```mermaid\n{mermaid}\n```")

        st.header("📈 Progress")
        if st.session_state.logs:
            for log in st.session_state.logs[-5:]:
                st.text(f"{log['timestamp']} - Iter {log['iteration']}: {log['findings']} findings, {log['sections']} sections")

    # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📝 Research Query")

        query = st.text_area(
            "Enter your research question",
            placeholder="e.g., What are the latest advances in quantum computing?",
            height=100,
        )

        context = st.text_area(
            "Additional context (optional)",
            placeholder="Any additional context or constraints...",
            height=80,
        )

        start_button = st.button("🚀 Start Research", type="primary", use_container_width=True)

        if start_button and query:
            with st.spinner("Researching..."):
                asyncio.run(run_research_streaming(query, context, max_iterations))

    with col2:
        st.header("📊 Status")

        if st.session_state.research_state:
            state = st.session_state.research_state

            # Status metrics
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)

            with metrics_col1:
                st.metric("Iteration", f"{state.iteration}/{state.max_iterations}")
            with metrics_col2:
                st.metric("Findings", len(state.findings))
            with metrics_col3:
                st.metric("Sections", len(state.sections))
            with metrics_col4:
                st.metric("Cost", f"${state.cost.total_cost_usd:.4f}")

            # Review status
            if state.review:
                status_color = "🟢" if state.review.status.value == "passed" else "🔴"
                st.write(f"{status_color} Review: {state.review.score:.2f} - {state.review.status.value}")

    # Results section
    if st.session_state.research_state:
        state = st.session_state.research_state

        st.header("📄 Research Report")

        if state.report:
            # Show report in tabs
            tab1, tab2, tab3, tab4 = st.tabs(["Report", "Sources", "Plan", "Cost Details"])

            with tab1:
                st.markdown(state.report)

                # Download button
                st.download_button(
                    "📥 Download Report",
                    state.report,
                    file_name=f"research_{state.trace_id}.md",
                    mime="text/markdown",
                )

            with tab2:
                st.subheader("Sources")
                for i, source in enumerate(state.sources, 1):
                    with st.expander(f"{i}. {source.title}"):
                        st.write(f"**URL:** {source.url}")
                        st.write(f"**Relevance:** {source.relevance_score:.2f}")
                        st.write(f"**Content:** {source.content[:300]}...")

            with tab3:
                if state.plan:
                    st.subheader("Research Plan")
                    st.write(f"**Strategy:** {state.plan.strategy}")

                    st.write("**Sub-queries:**")
                    for q in state.plan.sub_queries:
                        st.write(f"- {q}")

                    st.write("**Expected Sections:**")
                    for s in state.plan.expected_sections:
                        st.write(f"- {s}")

            with tab4:
                st.subheader("Cost Breakdown")
                st.json(state.cost.to_dict())

        else:
            st.info("Research in progress... Check the progress in the sidebar.")


if __name__ == "__main__":
    main()
