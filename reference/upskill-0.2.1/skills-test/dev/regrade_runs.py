#!/usr/bin/env python3
"""
Regrade existing run artifacts with stricter validation and richer timing stats.

This reads the existing runs/results.csv, re-validates each run's YAML with the
updated assertions, and recomputes LLM vs tool time plus turn counts from the
conversation logs. A new CSV is written to runs/regraded_results.csv.

Usage:
    python dev/regrade_runs.py                    # Regrade runs/ folder
    python dev/regrade_runs.py runs-skill-v1     # Regrade specific folder
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional

from fast_agent import ConversationSummary
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

# Existing fieldnames from agent.py plus the new timing columns.
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


def _clean_row(row: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in row.items() if key in FIELDNAMES}


def find_yaml(run_folder: Path) -> Optional[Path]:
    """Locate the YAML output for a run."""
    candidate = run_folder / DEFAULT_OUTPUT_FILE
    if candidate.exists():
        return candidate
    workspace_candidate = run_folder / "workspace" / DEFAULT_OUTPUT_FILE
    if workspace_candidate.exists():
        return workspace_candidate
    yamls = [p for p in run_folder.rglob("*.yaml")]
    return yamls[0] if yamls else None


def _latest_history_file(session_dir: Path) -> Optional[Path]:
    candidates = sorted(
        session_dir.glob("history_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def resolve_history_path(run_folder: Path, row: dict[str, str]) -> Optional[Path]:
    """Resolve the history log path using session info or legacy conversation.json."""
    history_file = row.get("session_history_file")
    if history_file:
        history_path = Path(history_file)
        if history_path.exists():
            return history_path

    session_id = row.get("session_id")
    if session_id:
        session_dir = run_folder / ".fast-agent" / "sessions" / session_id
        if session_dir.exists():
            latest = _latest_history_file(session_dir)
            if latest:
                return latest

    legacy_path = run_folder / "conversation.json"
    if legacy_path.exists():
        return legacy_path

    return None


def summarize_conversation(conversation_path: Path) -> tuple[float, float, int]:
    """Return (llm_time_ms, tool_time_ms, turns) from a conversation log."""
    if not conversation_path.exists():
        return 0.0, 0.0, 0

    messages = load_messages(str(conversation_path))
    summary = ConversationSummary(messages=messages)

    llm_time_ms = round(summary.total_elapsed_time_ms, 2)
    span_ms = summary.conversation_span_ms
    tool_time_ms = round(max(span_ms - llm_time_ms, 0.0), 2)
    turns = summary.user_message_count
    return llm_time_ms, tool_time_ms, turns


def regrade(runs_folder: Path):
    """Regrade all runs in the specified folder."""
    # Prefer results.csv, fall back to regraded_results.csv
    results_path = runs_folder / "results.csv"
    if not results_path.exists():
        results_path = runs_folder / "regraded_results.csv"
    output_path = runs_folder / "regraded_results_new.csv"

    assert results_path.exists(), f"Source results CSV not found at {runs_folder}"

    with open(results_path, newline="") as infile, open(output_path, "w", newline="") as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
        writer.writeheader()

        for row in reader:
            cleaned_row = _clean_row(row)
            batch_id = cleaned_row.get("batch_id", "")
            run_number = cleaned_row.get("run_number", "")
            run_folder = runs_folder / batch_id / f"run_{run_number}"
            history_path = resolve_history_path(run_folder, cleaned_row)
            yaml_path = find_yaml(run_folder)

            if history_path is not None:
                llm_time_ms, tool_time_ms, turns = summarize_conversation(history_path)
            else:
                llm_time_ms, tool_time_ms, turns = 0.0, 0.0, 0

            # Start with the original row, but override with new grades and timing.
            new_row = {**cleaned_row}
            new_row["llm_time_ms"] = llm_time_ms
            new_row["tool_time_ms"] = tool_time_ms
            new_row["turns"] = turns

            if yaml_path is None:
                new_row.update(
                    {
                        "passed": False,
                        "assertions_passed": 0,
                        "assertions_total": ASSERTIONS_TOTAL,
                        "metrics_count": 0,
                        "benchmarks_found": "",
                        "error_message": "Output YAML not found",
                    }
                )
                writer.writerow(new_row)
                continue

            validation: ValidationResult = validate_with_metrics(
                yaml_path,
                expected_metrics=EXPECTED_METRICS,
            )

            new_row.update(
                {
                    "passed": validation.passed,
                    "assertions_passed": validation.assertions_passed,
                    "assertions_total": validation.assertions_total,
                    "metrics_count": validation.metrics_count,
                    "benchmarks_found": ",".join(validation.benchmarks_found),
                    "error_message": validation.error_message or "",
                }
            )

            writer.writerow(new_row)

    print(f"Regraded results written to {output_path}")

    # Replace old regraded file with new one
    final_path = runs_folder / "regraded_results.csv"
    output_path.replace(final_path)
    print(f"Renamed to {final_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regrade run artifacts with updated validation.")
    parser.add_argument(
        "runs_folder",
        nargs="?",
        default="runs",
        help="Folder containing runs (default: runs)",
    )
    args = parser.parse_args()
    regrade(Path(args.runs_folder))
