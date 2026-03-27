#!/usr/bin/env python3
"""
Summarize run artifacts into a results CSV.

This script walks a runs/ folder, finds run artifacts (workspace output +
session history), recomputes validation metrics, and writes a fresh CSV.

Usage:
    python dev/summarize_runs.py                 # Summarize runs/ folder
    python dev/summarize_runs.py runs-skill-v1   # Summarize a specific folder
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fast_agent import ConversationSummary
from fast_agent.constants import FAST_AGENT_USAGE
from fast_agent.mcp.helpers.content_helpers import get_text
from fast_agent.mcp.prompt_serialization import load_messages

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from test_eval_assertions import (  # noqa: E402
    ASSERTIONS_TOTAL,
    EXPECTED_METRICS,
    ValidationResult,
    validate_with_metrics,
)


DEFAULT_OUTPUT_FILE = "olmo_7b_evaluations.yaml"

FIELDNAMES = [
    "batch_id",
    "run_number",
    "model",
    "timestamp",
    "passed",
    "assertions_passed",
    "assertions_total",
    "metrics_count",
    "benchmarks_found",
    "tokens",
    "conversation_span_ms",
    "tool_calls",
    "tool_errors",
    "mcp_calls",
    "mcp_errors",
    "execute_calls",
    "execute_errors",
    "error_message",
    "llm_time_ms",
    "tool_time_ms",
    "turns",
    "session_id",
    "session_history_file",
]


@dataclass
class SessionInfo:
    session_id: str
    created_at: str | None
    history_file: Path | None


@dataclass
class ConversationStats:
    conversation_span_ms: float
    llm_time_ms: float
    tool_time_ms: float
    turns: int
    tool_calls: int
    tool_errors: int
    tool_call_map: dict[str, int]
    tool_error_map: dict[str, int]
    tokens: int


def categorize_tool_calls(
    tool_call_map: dict[str, int],
    tool_error_map: dict[str, int],
) -> dict[str, int]:
    """Categorize tool calls and errors into MCP vs execute."""
    mcp_calls = 0
    mcp_errors = 0
    execute_calls = 0
    execute_errors = 0

    for tool_name, count in tool_call_map.items():
        if "__" in tool_name:
            mcp_calls += count
        else:
            execute_calls += count

    for tool_name, count in tool_error_map.items():
        if "__" in tool_name:
            mcp_errors += count
        else:
            execute_errors += count

    return {
        "mcp_calls": mcp_calls,
        "mcp_errors": mcp_errors,
        "execute_calls": execute_calls,
        "execute_errors": execute_errors,
    }


def find_yaml(run_folder: Path, output_filename: str) -> Optional[Path]:
    """Locate the YAML output for a run."""
    candidates = [
        run_folder / output_filename,
        run_folder / "workspace" / output_filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    yaml_files = [p for p in run_folder.rglob("*.yaml")]
    return yaml_files[0] if yaml_files else None


def _latest_history_file(session_dir: Path) -> Optional[Path]:
    candidates = sorted(
        session_dir.glob("history_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _load_session_info(session_dir: Path) -> SessionInfo:
    session_file = session_dir / "session.json"
    created_at = None
    if session_file.exists():
        try:
            payload = json.loads(session_file.read_text(encoding="utf-8"))
            created_at = payload.get("created_at")
        except json.JSONDecodeError:
            created_at = None
    history_file = _latest_history_file(session_dir)
    return SessionInfo(
        session_id=session_dir.name,
        created_at=created_at,
        history_file=history_file,
    )


def load_run_metadata(run_folder: Path) -> dict[str, object]:
    metadata_path = run_folder / "run_metadata.json"
    if not metadata_path.exists():
        return {}
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _session_roots(run_folder: Path) -> list[Path]:
    return [
        run_folder / "sessions",
        run_folder / ".fast-agent" / "sessions",
        run_folder.parent / "sessions" / run_folder.name,
    ]


def resolve_session_info(run_folder: Path) -> Optional[SessionInfo]:
    for sessions_root in _session_roots(run_folder):
        if not sessions_root.exists():
            continue

        session_dirs = [p for p in sessions_root.iterdir() if p.is_dir()]
        if not session_dirs:
            continue

        session_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        return _load_session_info(session_dirs[0])

    return None


def resolve_history_path(run_folder: Path) -> Optional[Path]:
    session_info = resolve_session_info(run_folder)
    if session_info and session_info.history_file:
        return session_info.history_file
    legacy_path = run_folder / "conversation.json"
    if legacy_path.exists():
        return legacy_path
    return None


def _extract_usage_tokens(messages: list) -> int:
    for message in reversed(messages):
        if message.role != "assistant":
            continue
        channels = message.channels or {}
        blocks = channels.get(FAST_AGENT_USAGE)
        if not blocks:
            continue
        usage_text = get_text(blocks[0])
        if not usage_text:
            continue
        try:
            payload = json.loads(usage_text)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        summary = payload.get("summary")
        if isinstance(summary, dict):
            tokens = summary.get("cumulative_billing_tokens")
            if isinstance(tokens, (int, float)):
                return int(tokens)
    return 0


def summarize_conversation(history_path: Optional[Path]) -> ConversationStats:
    if not history_path or not history_path.exists():
        return ConversationStats(
            conversation_span_ms=0.0,
            llm_time_ms=0.0,
            tool_time_ms=0.0,
            turns=0,
            tool_calls=0,
            tool_errors=0,
            tool_call_map={},
            tool_error_map={},
            tokens=0,
        )

    messages = load_messages(str(history_path))
    summary = ConversationSummary(messages=messages)
    tokens = _extract_usage_tokens(messages)

    llm_time_ms = round(summary.total_elapsed_time_ms, 2)
    span_ms = summary.conversation_span_ms
    tool_time_ms = round(max(span_ms - llm_time_ms, 0.0), 2)

    return ConversationStats(
        conversation_span_ms=span_ms,
        llm_time_ms=llm_time_ms,
        tool_time_ms=tool_time_ms,
        turns=summary.user_message_count,
        tool_calls=summary.tool_calls,
        tool_errors=summary.tool_errors,
        tool_call_map=summary.tool_call_map,
        tool_error_map=summary.tool_error_map,
        tokens=tokens,
    )


def iter_run_folders(runs_folder: Path) -> list[Path]:
    run_folders: list[Path] = []
    for batch_dir in sorted(p for p in runs_folder.iterdir() if p.is_dir()):
        if not any(child.name.startswith("run_") for child in batch_dir.iterdir()):
            continue
        for run_dir in sorted(batch_dir.glob("run_*")):
            if run_dir.is_dir():
                run_folders.append(run_dir)
    return run_folders


def summarize_runs(runs_folder: Path, output_path: Path, output_filename: str) -> None:
    run_folders = iter_run_folders(runs_folder)
    if not run_folders:
        raise FileNotFoundError(f"No run folders found under {runs_folder}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
        writer.writeheader()

        for run_folder in run_folders:
            batch_id = run_folder.parent.name
            run_number = run_folder.name.replace("run_", "")

            session_info = resolve_session_info(run_folder)
            history_path = resolve_history_path(run_folder)
            summary = summarize_conversation(history_path)
            tool_categories = categorize_tool_calls(
                summary.tool_call_map,
                summary.tool_error_map,
            )

            yaml_path = find_yaml(run_folder, output_filename)
            if yaml_path is None:
                validation = ValidationResult(
                    passed=False,
                    assertions_passed=0,
                    assertions_total=ASSERTIONS_TOTAL,
                    metrics_count=0,
                    benchmarks_found=[],
                    error_message="Output YAML not found",
                )
            else:
                validation = validate_with_metrics(
                    yaml_path,
                    expected_metrics=EXPECTED_METRICS,
                )

            run_metadata = load_run_metadata(run_folder)
            model_name = run_metadata.get("model")
            if not isinstance(model_name, str):
                model_name = ""

            row = {
                "batch_id": batch_id,
                "run_number": run_number,
                "model": model_name,
                "timestamp": session_info.created_at if session_info else "",
                "passed": validation.passed,
                "assertions_passed": validation.assertions_passed,
                "assertions_total": validation.assertions_total,
                "metrics_count": validation.metrics_count,
                "benchmarks_found": ",".join(validation.benchmarks_found),
                "tokens": summary.tokens,
                "conversation_span_ms": summary.conversation_span_ms,
                "tool_calls": summary.tool_calls,
                "tool_errors": summary.tool_errors,
                "mcp_calls": tool_categories["mcp_calls"],
                "mcp_errors": tool_categories["mcp_errors"],
                "execute_calls": tool_categories["execute_calls"],
                "execute_errors": tool_categories["execute_errors"],
                "error_message": validation.error_message or "",
                "llm_time_ms": summary.llm_time_ms,
                "tool_time_ms": summary.tool_time_ms,
                "turns": summary.turns,
                "session_id": session_info.session_id if session_info else "",
                "session_history_file": str(history_path) if history_path else "",
            }
            writer.writerow(row)

    print(f"Summary written to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize run artifacts into a CSV.")
    parser.add_argument(
        "runs_folder",
        nargs="?",
        default="runs",
        help="Folder containing runs (default: runs)",
    )
    parser.add_argument(
        "--output",
        default="runs/summarized_results.csv",
        help="Output CSV path (default: runs/summarized_results.csv)",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT_FILE,
        help="Name of the YAML results file (default: olmo_7b_evaluations.yaml)",
    )
    args = parser.parse_args()
    summarize_runs(
        Path(args.runs_folder),
        Path(args.output),
        args.output_file,
    )
