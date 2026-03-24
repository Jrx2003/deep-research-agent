"""Storage utilities for Deep Research Agent."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.core.state import ResearchState
from src.core.config import settings


def ensure_output_dir() -> Path:
    """Ensure output directory exists."""
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem."""
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename


def save_report(state: ResearchState, filename: Optional[str] = None) -> str:
    """Save research report to file.

    Args:
        state: Research state with report
        filename: Optional filename (default: auto-generated)

    Returns:
        Path to saved file
    """
    output_dir = ensure_output_dir()

    if filename is None:
        # Auto-generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_slug = sanitize_filename(state.query.replace(" ", "_")[:30])
        filename = f"{timestamp}_{query_slug}.md"

    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(state.report or "No report generated")

    return str(filepath)


def save_state(state: ResearchState, filename: Optional[str] = None) -> str:
    """Save research state to JSON file.

    Args:
        state: Research state
        filename: Optional filename (default: auto-generated)

    Returns:
        Path to saved file
    """
    output_dir = ensure_output_dir()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_slug = sanitize_filename(state.query.replace(" ", "_")[:30])
        filename = f"{timestamp}_{query_slug}_state.json"

    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

    return str(filepath)


def load_state(filepath: str) -> Optional[Dict[str, Any]]:
    """Load research state from JSON file.

    Args:
        filepath: Path to state file

    Returns:
        State dictionary or None if failed
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load state: {e}")
        return None


def export_to_json(state: ResearchState, filename: Optional[str] = None) -> str:
    """Export complete research to JSON.

    Args:
        state: Research state
        filename: Optional filename

    Returns:
        Path to saved file
    """
    output_dir = ensure_output_dir()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_slug = sanitize_filename(state.query.replace(" ", "_")[:30])
        filename = f"{timestamp}_{query_slug}_export.json"

    filepath = output_dir / filename

    export_data = {
        "query": state.query,
        "trace_id": state.trace_id,
        "started_at": state.started_at.isoformat(),
        "completed_at": datetime.now().isoformat(),
        "iterations": state.iteration,
        "plan": state.plan.to_dict() if state.plan else None,
        "findings": [f.to_dict() for f in state.findings],
        "sections": [s.to_dict() for s in state.sections],
        "review": state.review.to_dict() if state.review else None,
        "report": state.report,
        "sources": [s.to_dict() for s in state.sources],
        "cost": state.cost.to_dict(),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    return str(filepath)
