#!/usr/bin/env python3
"""Generate comparison charts for runs vs runs-skill-v1."""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_data(folder: str) -> dict:
    """Load and aggregate results by model."""
    with open(f"{folder}/regraded_results.csv") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(int(r["assertions_passed"]))

    return {
        model: {
            "avg": sum(scores) / len(scores),
            "passed": sum(1 for s in scores if s == 23),
            "total": len(scores),
            "pass_rate": sum(1 for s in scores if s == 23) / len(scores) * 100,
            "scores": scores,
        }
        for model, scores in by_model.items()
    }


def shorten_model_name(name: str) -> str:
    """Shorten model names for display."""
    replacements = {
        "moonshotai/Kimi-K2-Instruct-0905-": "Kimi-K2-",
        "moonshotai/Kimi-K2-Instruct-0905": "Kimi-K2",
        "MiniMaxAI/MiniMax-M2": "MiniMax-M2",
        "openai/gpt-oss-120b": "gpt-oss-120b",
        "zai-org/GLM-4.6": "GLM-4.6",
        "grok-4-fast-non-reasoning": "grok-4-fast",
        "gpt-5-mini-(local-skills)": "gpt-5-mini (local)",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name


def create_comparison_charts(output_path: str = "comparison_charts.png"):
    """Create comparison charts between runs and runs-skill-v1."""
    runs_data = load_data("runs")
    skill_v1_data = load_data("runs-skill-v1")

    # Find models that appear in both datasets
    common_models = set(runs_data.keys()) & set(skill_v1_data.keys())
    runs_only = set(runs_data.keys()) - common_models
    skill_v1_only = set(skill_v1_data.keys()) - common_models

    # Include all models from runs (common + runs-only), sorted by runs avg score
    all_runs_models = sorted(runs_data.keys(), key=lambda m: -runs_data[m]["avg"])

    # Sort common models by runs avg score (for delta chart)
    common_models = sorted(common_models, key=lambda m: -runs_data[m]["avg"])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Model Performance Comparison: Current (runs) vs Skill-v1",
        fontsize=14,
        fontweight="bold",
    )

    # Color scheme
    runs_color = "#2E86AB"  # Blue
    skill_v1_color = "#A23B72"  # Purple

    # Chart 1: Average Score Comparison (all runs models)
    ax1 = axes[0, 0]
    x = np.arange(len(all_runs_models))
    width = 0.35
    short_names = [shorten_model_name(m) for m in all_runs_models]

    bars1 = ax1.bar(
        x - width / 2,
        [runs_data[m]["avg"] for m in all_runs_models],
        width,
        label="Current (runs)",
        color=runs_color,
    )
    # For skill-v1, draw bars with different alpha for missing models
    skill_v1_avgs = [skill_v1_data[m]["avg"] if m in skill_v1_data else 0 for m in all_runs_models]
    bars2 = ax1.bar(
        x + width / 2,
        skill_v1_avgs,
        width,
        label="Skill-v1",
        color=skill_v1_color,
    )
    # Dim bars for models not in skill-v1
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars2[i].set_alpha(0.3)

    ax1.set_ylabel("Average Score (out of 23)")
    ax1.set_title("Average Assertion Score by Model")
    ax1.set_xticks(x)
    ax1.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax1.legend()
    ax1.set_ylim(0, 25)
    ax1.axhline(y=23, color="green", linestyle="--", alpha=0.5, label="Perfect")

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(
            f"{height:.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        if all_runs_models[i] in skill_v1_data:
            ax1.annotate(
                f"{height:.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        else:
            ax1.annotate(
                "N/A",
                xy=(bar.get_x() + bar.get_width() / 2, 1),
                xytext=(0, 0),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7,
                color="gray",
            )

    # Chart 2: Pass Rate Comparison (all runs models)
    ax2 = axes[0, 1]
    bars1 = ax2.bar(
        x - width / 2,
        [runs_data[m]["pass_rate"] for m in all_runs_models],
        width,
        label="Current (runs)",
        color=runs_color,
    )
    skill_v1_pass_rates = [skill_v1_data[m]["pass_rate"] if m in skill_v1_data else 0 for m in all_runs_models]
    bars2 = ax2.bar(
        x + width / 2,
        skill_v1_pass_rates,
        width,
        label="Skill-v1",
        color=skill_v1_color,
    )
    # Dim bars for models not in skill-v1
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars2[i].set_alpha(0.3)

    ax2.set_ylabel("Pass Rate (%)")
    ax2.set_title("Pass Rate by Model (23/23 assertions)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax2.legend()
    ax2.set_ylim(0, 110)

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax2.annotate(
            f"{height:.0f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        if all_runs_models[i] in skill_v1_data:
            ax2.annotate(
                f"{height:.0f}%",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        else:
            ax2.annotate(
                "N/A",
                xy=(bar.get_x() + bar.get_width() / 2, 2),
                xytext=(0, 0),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7,
                color="gray",
            )

    # Chart 3: Improvement/Regression (delta) - for all runs models
    ax3 = axes[1, 0]
    deltas = []
    for m in all_runs_models:
        if m in skill_v1_data:
            deltas.append(runs_data[m]["avg"] - skill_v1_data[m]["avg"])
        else:
            deltas.append(0)  # No comparison available
    colors = [runs_color if d >= 0 else skill_v1_color for d in deltas]
    bars = ax3.bar(x, deltas, color=colors)
    # Dim bars for models not in skill-v1
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars[i].set_alpha(0.3)
    ax3.set_ylabel("Score Change (Current - Skill-v1)")
    ax3.set_title("Score Improvement/Regression")
    ax3.set_xticks(x)
    ax3.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax3.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    for i, (bar, delta) in enumerate(zip(bars, deltas)):
        height = bar.get_height()
        if all_runs_models[i] in skill_v1_data:
            ax3.annotate(
                f"{delta:+.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height >= 0 else -12),
                textcoords="offset points",
                ha="center",
                va="bottom" if height >= 0 else "top",
                fontsize=9,
                fontweight="bold",
            )
        else:
            ax3.annotate(
                "NEW",
                xy=(bar.get_x() + bar.get_width() / 2, 0.5),
                xytext=(0, 0),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color="gray",
            )

    # Chart 4: All models overview
    ax4 = axes[1, 1]

    # Combine all models
    all_models_runs = sorted(runs_data.keys(), key=lambda m: -runs_data[m]["avg"])
    all_models_skill = sorted(
        skill_v1_data.keys(), key=lambda m: -skill_v1_data[m]["avg"]
    )

    # Create a summary table-like visualization
    ax4.axis("off")

    table_data = []
    headers = ["Model", "Current Avg", "Skill-v1 Avg", "Delta"]

    for m in common_models:
        delta = runs_data[m]["avg"] - skill_v1_data[m]["avg"]
        table_data.append(
            [
                shorten_model_name(m),
                f"{runs_data[m]['avg']:.1f}",
                f"{skill_v1_data[m]['avg']:.1f}",
                f"{delta:+.1f}",
            ]
        )

    # Add runs-only models
    for m in sorted(runs_only, key=lambda m: -runs_data[m]["avg"]):
        table_data.append(
            [shorten_model_name(m), f"{runs_data[m]['avg']:.1f}", "—", "NEW"]
        )

    # Add skill-v1-only models
    for m in sorted(skill_v1_only, key=lambda m: -skill_v1_data[m]["avg"]):
        table_data.append(
            [shorten_model_name(m), "—", f"{skill_v1_data[m]['avg']:.1f}", "OLD"]
        )

    table = ax4.table(
        cellText=table_data,
        colLabels=headers,
        loc="center",
        cellLoc="center",
        colColours=[runs_color + "40"] * 4,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    ax4.set_title("Full Model Comparison Summary", pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Chart saved to {output_path}")

    # Also save individual charts
    return fig


def create_timing_charts(output_path: str = "timing_charts.png"):
    """Create timing comparison charts between runs and runs-skill-v1."""
    runs_data = load_timing_data("runs")
    skill_v1_data = load_timing_data("runs-skill-v1")

    # Include all models from runs, sorted by runs avg score (reuse score sorting)
    score_data = load_data("runs")
    all_runs_models = sorted(score_data.keys(), key=lambda m: -score_data[m]["avg"])

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(
        "Timing & Efficiency Comparison: Current (runs) vs Skill-v1",
        fontsize=14,
        fontweight="bold",
    )

    # Color scheme
    runs_color = "#2E86AB"  # Blue
    skill_v1_color = "#A23B72"  # Purple

    x = np.arange(len(all_runs_models))
    width = 0.35
    short_names = [shorten_model_name(m) for m in all_runs_models]

    # Chart 1: LLM Time Comparison
    ax1 = axes[0, 0]
    bars1 = ax1.bar(
        x - width / 2,
        [runs_data[m]["avg_llm_time_s"] for m in all_runs_models],
        width,
        label="Current (runs)",
        color=runs_color,
    )
    skill_v1_times = [skill_v1_data[m]["avg_llm_time_s"] if m in skill_v1_data else 0 for m in all_runs_models]
    bars2 = ax1.bar(
        x + width / 2,
        skill_v1_times,
        width,
        label="Skill-v1",
        color=skill_v1_color,
    )
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars2[i].set_alpha(0.3)

    ax1.set_ylabel("LLM Time (seconds)")
    ax1.set_title("Average LLM Processing Time")
    ax1.set_xticks(x)
    ax1.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax1.legend()

    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(
            f"{height:.0f}s",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for i, bar in enumerate(bars2):
        if all_runs_models[i] in skill_v1_data:
            height = bar.get_height()
            ax1.annotate(
                f"{height:.0f}s",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    # Chart 2: Turns Comparison
    ax2 = axes[0, 1]
    bars1 = ax2.bar(
        x - width / 2,
        [runs_data[m]["avg_turns"] for m in all_runs_models],
        width,
        label="Current (runs)",
        color=runs_color,
    )
    skill_v1_turns = [skill_v1_data[m]["avg_turns"] if m in skill_v1_data else 0 for m in all_runs_models]
    bars2 = ax2.bar(
        x + width / 2,
        skill_v1_turns,
        width,
        label="Skill-v1",
        color=skill_v1_color,
    )
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars2[i].set_alpha(0.3)

    ax2.set_ylabel("Number of Turns")
    ax2.set_title("Average Conversation Turns")
    ax2.set_xticks(x)
    ax2.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax2.legend()

    for bar in bars1:
        height = bar.get_height()
        ax2.annotate(
            f"{height:.1f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for i, bar in enumerate(bars2):
        if all_runs_models[i] in skill_v1_data:
            height = bar.get_height()
            ax2.annotate(
                f"{height:.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    # Chart 3: LLM Time Change (delta)
    ax3 = axes[1, 0]
    deltas = []
    for m in all_runs_models:
        if m in skill_v1_data:
            deltas.append(runs_data[m]["avg_llm_time_s"] - skill_v1_data[m]["avg_llm_time_s"])
        else:
            deltas.append(0)
    # For time, negative is better (faster)
    colors = ["#28a745" if d < 0 else "#dc3545" for d in deltas]
    bars = ax3.bar(x, deltas, color=colors)
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars[i].set_alpha(0.3)
            bars[i].set_color("gray")

    ax3.set_ylabel("Time Change (seconds)")
    ax3.set_title("LLM Time Change (negative = faster)")
    ax3.set_xticks(x)
    ax3.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax3.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    for i, (bar, delta) in enumerate(zip(bars, deltas)):
        if all_runs_models[i] in skill_v1_data:
            height = bar.get_height()
            ax3.annotate(
                f"{delta:+.0f}s",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height >= 0 else -12),
                textcoords="offset points",
                ha="center",
                va="bottom" if height >= 0 else "top",
                fontsize=9,
                fontweight="bold",
            )
        else:
            ax3.annotate(
                "NEW",
                xy=(bar.get_x() + bar.get_width() / 2, 0.5),
                ha="center",
                va="bottom",
                fontsize=8,
                color="gray",
            )

    # Chart 4: Turns Change (delta)
    ax4 = axes[1, 1]
    deltas = []
    for m in all_runs_models:
        if m in skill_v1_data:
            deltas.append(runs_data[m]["avg_turns"] - skill_v1_data[m]["avg_turns"])
        else:
            deltas.append(0)
    # For turns, negative is better (fewer turns)
    colors = ["#28a745" if d < 0 else "#dc3545" for d in deltas]
    bars = ax4.bar(x, deltas, color=colors)
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars[i].set_alpha(0.3)
            bars[i].set_color("gray")

    ax4.set_ylabel("Turns Change")
    ax4.set_title("Turns Change (negative = fewer turns)")
    ax4.set_xticks(x)
    ax4.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax4.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    for i, (bar, delta) in enumerate(zip(bars, deltas)):
        if all_runs_models[i] in skill_v1_data:
            height = bar.get_height()
            ax4.annotate(
                f"{delta:+.1f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height >= 0 else -12),
                textcoords="offset points",
                ha="center",
                va="bottom" if height >= 0 else "top",
                fontsize=9,
                fontweight="bold",
            )
        else:
            ax4.annotate(
                "NEW",
                xy=(bar.get_x() + bar.get_width() / 2, 0.1),
                ha="center",
                va="bottom",
                fontsize=8,
                color="gray",
            )

    # Chart 5: Token Usage Comparison
    ax5 = axes[0, 2]
    bars1 = ax5.bar(
        x - width / 2,
        [runs_data[m]["avg_tokens_k"] for m in all_runs_models],
        width,
        label="Current (runs)",
        color=runs_color,
    )
    skill_v1_tokens = [skill_v1_data[m]["avg_tokens_k"] if m in skill_v1_data else 0 for m in all_runs_models]
    bars2 = ax5.bar(
        x + width / 2,
        skill_v1_tokens,
        width,
        label="Skill-v1",
        color=skill_v1_color,
    )
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars2[i].set_alpha(0.3)

    ax5.set_ylabel("Tokens (thousands)")
    ax5.set_title("Average Token Usage")
    ax5.set_xticks(x)
    ax5.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax5.legend()

    for bar in bars1:
        height = bar.get_height()
        ax5.annotate(
            f"{height:.0f}k",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for i, bar in enumerate(bars2):
        if all_runs_models[i] in skill_v1_data:
            height = bar.get_height()
            ax5.annotate(
                f"{height:.0f}k",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    # Chart 6: Token Usage Change (delta)
    ax6 = axes[1, 2]
    deltas = []
    for m in all_runs_models:
        if m in skill_v1_data:
            deltas.append(runs_data[m]["avg_tokens_k"] - skill_v1_data[m]["avg_tokens_k"])
        else:
            deltas.append(0)
    # For tokens, negative is better (fewer tokens)
    colors = ["#28a745" if d < 0 else "#dc3545" for d in deltas]
    bars = ax6.bar(x, deltas, color=colors)
    for i, m in enumerate(all_runs_models):
        if m not in skill_v1_data:
            bars[i].set_alpha(0.3)
            bars[i].set_color("gray")

    ax6.set_ylabel("Token Change (thousands)")
    ax6.set_title("Token Usage Change (negative = fewer tokens)")
    ax6.set_xticks(x)
    ax6.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax6.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    for i, (bar, delta) in enumerate(zip(bars, deltas)):
        if all_runs_models[i] in skill_v1_data:
            height = bar.get_height()
            ax6.annotate(
                f"{delta:+.0f}k",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height >= 0 else -12),
                textcoords="offset points",
                ha="center",
                va="bottom" if height >= 0 else "top",
                fontsize=9,
                fontweight="bold",
            )
        else:
            ax6.annotate(
                "NEW",
                xy=(bar.get_x() + bar.get_width() / 2, 1),
                ha="center",
                va="bottom",
                fontsize=8,
                color="gray",
            )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Timing chart saved to {output_path}")
    return fig


def load_timing_data(folder: str) -> dict:
    """Load timing data aggregated by model."""
    with open(f"{folder}/regraded_results.csv") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append({
            "llm_time_ms": float(r["llm_time_ms"]) if r["llm_time_ms"] else 0,
            "turns": int(r["turns"]) if r["turns"] else 0,
            "tokens": int(r["tokens"]) if r["tokens"] else 0,
        })

    return {
        model: {
            "avg_llm_time_s": sum(d["llm_time_ms"] for d in data) / len(data) / 1000,
            "avg_turns": sum(d["turns"] for d in data) / len(data),
            "avg_tokens_k": sum(d["tokens"] for d in data) / len(data) / 1000,
        }
        for model, data in by_model.items()
    }


if __name__ == "__main__":
    create_comparison_charts()
    create_timing_charts()
