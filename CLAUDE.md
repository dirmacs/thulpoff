# thulpoff

Skill distillation for AI agents. Generate, evaluate, and refine SKILL.md files using teacher-student model distillation. 4-crate Rust workspace.

## Build & Test

```bash
cargo build --workspace
cargo test --workspace          # 36 tests
```

## Architecture

- `thulpoff-core` (8 tests) — types, traits, LlmProvider, CompletionRequest/Response
- `thulpoff-provider` (8 tests) — AnthropicProvider (Claude), NimProvider (NVIDIA NIM)
- `thulpoff-engine` (14 tests) — GenerationEngine, EvaluationEngine, RefinementEngine
- `thulpoff-cli` (6 tests) — generate, eval, refine, list commands

## Conventions

- Git author: `bkataru <baalateja.k@gmail.com>`
- Three-phase loop: generate → evaluate → refine
- Requires ANTHROPIC_API_KEY or NVIDIA_API_KEY
- Output: SKILL.md files compatible with Claude Code and thulp
