# thulpoff-core

Core types and traits for the Thulpoff skill distillation framework.

Thulpoff generates and refines SKILL.md files via LLM distillation from agent sessions — the teacher-student upskill paradigm applied to AI coding agents.

## Key Types

- `TeacherSession` — A recorded agent session to learn from
- `SkillDraft` — Generated skill content with metadata
- `EvalResult` — Quality evaluation of a generated skill
- `LlmProvider` — Trait for pluggable LLM backends

## License

MIT
