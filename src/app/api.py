"""FastAPI server for Deep Research Agent."""

from typing import Optional, List
from dataclasses import asdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.state import ResearchState
from src.core.graph import create_research_graph
from src.agents import (
    planner_node,
    researcher_node,
    synthesis_node,
    critic_node,
    writer_node,
)
from src.tools.storage import save_report, save_state


# In-memory storage for research sessions (replace with Redis in production)
research_sessions: dict[str, ResearchState] = {}


class ResearchRequest(BaseModel):
    """Research request."""

    query: str = Field(..., description="Research query")
    context: Optional[str] = Field(None, description="Additional context")
    max_iterations: int = Field(3, ge=1, le=5, description="Maximum iterations")


class ResearchResponse(BaseModel):
    """Research response."""

    trace_id: str
    status: str
    message: str


class ResearchStatus(BaseModel):
    """Research status."""

    trace_id: str
    status: str
    query: str
    iteration: int
    max_iterations: int
    has_plan: bool
    findings_count: int
    sections_count: int
    review_status: Optional[str]
    review_score: Optional[float]
    is_complete: bool
    cost_usd: float


class ResearchResult(BaseModel):
    """Research result."""

    trace_id: str
    query: str
    status: str
    report: Optional[str]
    sources: List[dict]
    cost: dict
    iterations: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting Deep Research Agent API")
    yield
    # Shutdown
    print("👋 Shutting down")


app = FastAPI(
    title="Deep Research Agent API",
    description="Multi-agent deep research system",
    version="0.1.0",
    lifespan=lifespan,
)


async def run_research_task(state: ResearchState):
    """Run research task in background."""
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
        # Update session storage
        research_sessions[state.trace_id] = event

    # Save outputs
    if final_state:
        save_report(final_state)
        save_state(final_state)


@app.post("/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new research task."""
    # Create initial state
    state = ResearchState(
        query=request.query,
        context=request.context,
        max_iterations=request.max_iterations,
    )

    # Store initial state
    research_sessions[state.trace_id] = state

    # Start background task
    background_tasks.add_task(run_research_task, state)

    return ResearchResponse(
        trace_id=state.trace_id,
        status="started",
        message="Research task started",
    )


@app.get("/research/{trace_id}/status", response_model=ResearchStatus)
async def get_research_status(trace_id: str):
    """Get research task status."""
    if trace_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Research task not found")

    state = research_sessions[trace_id]

    return ResearchStatus(
        trace_id=state.trace_id,
        status="running" if not state.is_complete() else "complete",
        query=state.query,
        iteration=state.iteration,
        max_iterations=state.max_iterations,
        has_plan=state.plan is not None,
        findings_count=len(state.findings),
        sections_count=len(state.sections),
        review_status=state.review.status.value if state.review else None,
        review_score=state.review.score if state.review else None,
        is_complete=state.is_complete(),
        cost_usd=state.cost.total_cost_usd,
    )


@app.get("/research/{trace_id}/result", response_model=ResearchResult)
async def get_research_result(trace_id: str):
    """Get research result."""
    if trace_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Research task not found")

    state = research_sessions[trace_id]

    return ResearchResult(
        trace_id=state.trace_id,
        query=state.query,
        status="complete" if state.is_complete() else "running",
        report=state.report,
        sources=[s.to_dict() for s in state.sources],
        cost=state.cost.to_dict(),
        iterations=state.iteration,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
