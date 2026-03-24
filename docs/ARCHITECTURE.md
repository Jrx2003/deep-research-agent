# Architecture Documentation

## System Overview

Deep Research Agent is built on a **multi-agent pipeline architecture** using LangGraph for orchestration.

## Core Design Principles

### 1. Separation of Concerns

Each agent has a single, well-defined responsibility:
- **Planner**: Strategic thinking, query decomposition
- **Researcher**: Information gathering, source collection
- **Synthesis**: Information integration, coherence building
- **Critic**: Quality assurance, gap identification
- **Writer**: Final output generation, formatting

### 2. Model Tier Strategy

Different tasks require different model capabilities:

| Tier | Models | Use Case | Cost Factor |
|------|--------|----------|-------------|
| Light | GPT-4o-mini, Claude Haiku | Search, extraction, formatting | 1x |
| Medium | GPT-4o, Claude Sonnet | Planning, synthesis, reasoning | 10x |
| Strong | o1, Claude Opus | Critic, final writing, complex analysis | 50x |

### 3. Stateful Execution

All agent communication happens through a shared state object:

```python
@dataclass
class ResearchState:
    # Input
    query: str
    context: Optional[str]

    # Execution
    plan: Optional[ResearchPlan]
    search_results: List[SearchResult]
    findings: List[Finding]
    sections: List[Section]
    review: Optional[ReviewResult]

    # Output
    report: Optional[str]
    sources: List[Source]

    # Metadata
    iteration: int = 0
    cost: CostTracker = field(default_factory=CostTracker)
    trace_id: Optional[str] = None
```

### 4. Feedback Loop

The Critic Agent can trigger a feedback loop:
- If review passes → proceed to Writer
- If review fails → return to Planner with feedback

Max iterations: 3 (configurable)

## Data Flow

```
┌─────────────┐
│   Input     │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│   Planner   │────▶│  Sub-queries    │
│   Agent     │     │  + Strategy     │
└──────┬──────┘     └─────────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│  Researcher │────▶│  Raw results    │
│   Agent     │     │  from search    │
└──────┬──────┘     └─────────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│  Synthesis  │────▶│  Coherent       │
│   Agent     │     │  sections       │
└──────┬──────┘     └─────────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│   Critic    │────▶│  Pass / Fail    │
│   Agent     │     │  + Feedback     │
└──────┬──────┘     └─────────────────┘
       │
       ├── Pass ──▶ Writer
       │
       └── Fail ──▶ Planner (loop)

┌─────────────┐
│   Writer    │────▶ Final Report
│   Agent     │
└─────────────┘
```

## Component Details

### Core Framework (`src/core/`)

#### State Management (`state.py`)
- Defines `ResearchState` dataclass
- Handles state serialization/deserialization
- Provides state validation

#### Graph Builder (`graph.py`)
- Constructs the LangGraph workflow
- Defines node connections
- Implements conditional edges

#### Model Router (`router.py`)
- Routes tasks to appropriate LLM
- Manages API keys and rate limits
- Tracks token usage

### Agents (`src/agents/`)

Each agent follows the same pattern:

```python
def agent_node(state: ResearchState) -> ResearchState:
    """Agent implementation."""
    # 1. Extract relevant state
    # 2. Call LLM with appropriate prompt
    # 3. Parse response
    # 4. Update state
    # 5. Return updated state
```

### Tools (`src/tools/`)

#### Search (`search.py`)
- DuckDuckGo search (free, no API key)
- SerpAPI (Google search, requires API key)
- Result deduplication

#### Scraper (`scraper.py`)
- Fetch webpage content
- Extract main text
- Handle JavaScript rendering (optional)

#### Storage (`storage.py`)
- Save/load research sessions
- Export to various formats (Markdown, PDF, JSON)

### Memory (`src/memory/`)

#### Vector Store (`vector_store.py`)
- ChromaDB integration
- Embedding model: sentence-transformers
- Semantic search across research history

## Observability

### Tracing

All agent executions are traced using LangSmith:

```python
@traceable(run_type="chain")
def agent_node(state: ResearchState) -> ResearchState:
    ...
```

### Cost Tracking

Each model call updates the cost tracker:

```python
@dataclass
class CostTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost_usd: float = 0.0
    calls_by_model: Dict[str, int] = field(default_factory=dict)
```

### Logging

Structured logging using `structlog`:

```python
logger = structlog.get_logger()
logger.info("agent_start", agent="planner", query=state.query)
```

## Deployment Options

### 1. CLI Tool

```bash
deep-research "quantum computing advances"
```

### 2. API Server

```bash
uvicorn src.app.api:app --host 0.0.0.0 --port 8000
```

API endpoints:
- `POST /research` - Start research
- `GET /research/{id}` - Get research status
- `GET /research/{id}/report` - Get final report

### 3. Streamlit UI

```bash
streamlit run src/app/ui.py
```

Web interface for interactive research.

## Scalability Considerations

### Batch Processing

For processing multiple topics:

```python
async def batch_research(queries: List[str]):
    tasks = [research(query) for query in queries]
    return await asyncio.gather(*tasks)
```

### Parallel Search

Multiple sub-queries can be searched in parallel:

```python
async def parallel_search(queries: List[str]):
    tasks = [search(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return flatten(results)
```

### Caching

- Search results cached for 1 hour
- LLM responses cached for identical prompts
- Vector embeddings cached in ChromaDB

## Security

- API keys stored in environment variables
- No sensitive data in logs
- Input validation on all user inputs
- Rate limiting on API endpoints
