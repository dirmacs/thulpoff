# thulpoff — Agent Guidelines

## What This Is

Thulpoff captures domain expertise from capable "teacher" models and encodes it into SKILL.md files for smaller "student" models. Three-phase distillation: generate → evaluate → refine.

## For Agents

- Run `cargo test --workspace` — 36 tests must pass
- LLM providers are abstracted — add new ones via the LlmProvider trait
- Engine crate has the core logic — generation, evaluation, refinement
- SKILL.md output must be valid for Claude Code skill format
- Don't hardcode model names — use provider configuration
