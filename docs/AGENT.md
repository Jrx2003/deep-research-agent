# AGENT.md - AI Tool Development Guide

> Progressive disclosure design for AI development tools.

---

## 🚀 Quick Start (5 minutes)

### What is this?

Deep Research Agent is a **multi-agent research system** that automates deep research tasks through a pipeline of specialized agents.

### Current Phase

**Phase 1: Infrastructure** - Project setup and scaffolding

### Run the project

```bash
cd ~/code/deep-research-agent
pip install -e ".[dev]"
python -m src.app.cli --help
```

### Key commands

```bash
# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/

# Type check
mypy src/
```

---

## 🎯 Current Focus

### Phase 1: Infrastructure (In Progress)

Tasks being worked on:
- [x] Project directory structure
- [x] pyproject.toml
- [x] AGENT.md initial version
- [ ] GitHub repository setup
- [ ] Core framework scaffolding

### Next immediate tasks

1. Create core state management (`src/core/state.py`)
2. Set up LangGraph base architecture (`src/core/graph.py`)
3. Implement model router (`src/core/router.py`)

---

## 🏗️ Architecture Overview

### Agent Pipeline

```
Planner → Researcher → Synthesis → Critic → Writer
   ↑                                    │
   └────────────────────────────────────┘ (feedback loop)
```

### Agent Responsibilities

| Agent | Purpose | Model Tier |
|-------|---------|------------|
| **Planner** | Break down research topic into sub-queries | Medium |
| **Researcher** | Execute searches and gather information | Light |
| **Synthesis** | Combine findings into coherent sections | Medium |
| **Critic** | Review quality and identify gaps | Strong |
| **Writer** | Produce final polished output | Strong |

### State Flow

```python
# Simplified state structure
class ResearchState:
    query: str                    # Original research query
    plan: ResearchPlan            # Planner output
    findings: List[Finding]       # Researcher output
    sections: List[Section]       # Synthesis output
    review: ReviewResult          # Critic output
    report: str                   # Writer output
    iterations: int               # Current iteration count
    cost: CostTracker             # Cost tracking
```

---

## 🔧 Deep Dive (Expand as needed)

### Model Routing Strategy

```python
# Router logic pseudocode
def route_task(task: Task) -> ModelTier:
    if task.type == "search" or task.type == "summarize":
        return LIGHT    # GPT-4o-mini, Haiku
    elif task.type == "plan" or task.type == "synthesis":
        return MEDIUM   # GPT-4o, Sonnet
    else:
        return STRONG   # o1, Opus
```

### LangGraph Structure

```python
# Graph definition pattern
graph = StateGraph(ResearchState)

# Add nodes
graph.add_node("planner", planner_node)
graph.add_node("researcher", researcher_node)
graph.add_node("synthesis", synthesis_node)
graph.add_node("critic", critic_node)
graph.add_node("writer", writer_node)

# Define edges
graph.add_edge(START, "planner")
graph.add_edge("planner", "researcher")
graph.add_edge("researcher", "synthesis")
graph.add_edge("synthesis", "critic")

# Conditional edge: loop back or finish
graph.add_conditional_edges(
    "critic",
    should_continue,
    {True: "writer", False: "planner"}
)
graph.add_edge("writer", END)
```

### Memory / Vector Store

- **Purpose**: Store research findings for retrieval and accumulation
- **Implementation**: ChromaDB with sentence-transformers embeddings
- **Collection**: One per research session
- **Metadata**: Source URL, retrieval time, confidence score

---

## ⚠️ Known Issues & TODOs

### Current

- [ ] Need to implement proper error handling for search failures
- [ ] Cost tracking not yet implemented
- [ ] Need to add retry logic for LLM calls

### Planned

- [ ] Add support for PDF/document ingestion
- [ ] Implement parallel search for sub-queries
- [ ] Add caching layer for search results

---

## 📚 Reference

### File Locations

| Component | Path |
|-----------|------|
| State definition | `src/core/state.py` |
| Graph builder | `src/core/graph.py` |
| Model router | `src/core/router.py` |
| Planner agent | `src/agents/planner.py` |
| Researcher agent | `src/agents/researcher.py` |
| Synthesis agent | `src/agents/synthesis.py` |
| Critic agent | `src/agents/critic.py` |
| Writer agent | `src/agents/writer.py` |
| Search tools | `src/tools/search.py` |
| Vector store | `src/memory/vector_store.py` |
| CLI entry | `src/app/cli.py` |
| API entry | `src/app/api.py` |
| UI entry | `src/app/ui.py` |

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Optional
SERPAPI_API_KEY=your_key_here  # For Google search
LANGCHAIN_API_KEY=your_key     # For LangSmith tracing
LANGCHAIN_PROJECT=deep-research-agent
```
