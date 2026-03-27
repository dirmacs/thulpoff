# thulpoff

> Rust implementation of skill distillation for AI agents

**thulpoff** is a Rust crate that implements HuggingFace's [upskill](https://github.com/huggingface/upskill) paradigm - a teacher-student model skill distillation framework. It generates, evaluates, and refines `SKILL.md` files that can be used with Claude Code, thulp, or any agent supporting the skill file format.

## What is Skill Distillation?

Skill distillation is the process of capturing domain expertise from a capable "teacher" model (like Claude Sonnet or GPT-4o) and encoding it into structured skill files that can enhance the performance of smaller, faster "student" models (like Haiku, Qwen, or local LLMs).

The workflow:
1. **Teacher demonstrates** - A capable model solves a challenging task
2. **Skill extraction** - The solution patterns are distilled into a SKILL.md file
3. **Test generation** - Test cases are created to validate skill effectiveness
4. **Student evaluation** - Student models are evaluated with and without the skill
5. **Refinement** - The skill is iteratively improved based on failure analysis

## Why Rust?

- **Performance** - Fast evaluation harness for running many test cases
- **Dirmacs ecosystem** - Integrates with [thulp](https://github.com/dirmacs/thulp), [ares](https://github.com/dirmacs/ares), [lancor](https://github.com/dirmacs/lancor)
- **Type safety** - Strong types for skill files, test cases, and evaluation results
- **Cross-platform** - Single binary distribution

## Status

**Pre-development** - This project is in the design phase. Implementation will begin after the `thulp-skill-files` crate is available in the thulp ecosystem.

See [DEPENDENCIES.md](./docs/DEPENDENCIES.md) for prerequisites.

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design and component overview |
| [CLI.md](./docs/CLI.md) | Command-line interface reference |
| [TYPES.md](./docs/TYPES.md) | Core data types and structures |
| [PROVIDERS.md](./docs/PROVIDERS.md) | LLM provider specifications |
| [DEPENDENCIES.md](./docs/DEPENDENCIES.md) | thulp prerequisites and integration |
| [ROADMAP.md](./docs/ROADMAP.md) | Implementation phases and timeline |
| [EXAMPLES.md](./docs/EXAMPLES.md) | Usage examples and workflows |

## Quick Preview

```bash
# Generate a CUDA kernel optimization skill using Claude as teacher
thulpoff generate \
  --task "Write an optimized CUDA kernel for matrix multiplication" \
  --name cuda-matmul \
  --model claude-sonnet-4-20250514 \
  --test-cases 10

# Evaluate the skill with a smaller model
thulpoff eval \
  --skill cuda-matmul \
  --model claude-3-5-haiku-20241022 \
  --baseline

# Evaluate with local model via Ollama
thulpoff eval \
  --skill cuda-matmul \
  --model qwen2.5-coder:32b \
  --provider openai-compat \
  --base-url http://localhost:11434/v1

# List all skills with evaluation results
thulpoff list --with-results
```

## Inspiration

This project is inspired by:
- [HuggingFace upskill](https://github.com/huggingface/upskill) - The original Python implementation
- [We Got Claude to Build CUDA Kernels and teach open models!](https://huggingface.co/blog/open-source-llms-as-agents-cuda-kernel) - HuggingFace blog post demonstrating the approach
- [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills) - The SKILL.md format

## License

MIT OR Apache-2.0

## Related Projects

- [thulp](https://github.com/dirmacs/thulp) - Execution Context Engineering Platform for AI Agents
- [ares](https://github.com/dirmacs/ares) - Production-grade agentic chatbot server
- [lancor](https://github.com/dirmacs/lancor) - Rust client for llama.cpp's OpenAI-compatible API
- [forge](https://github.com/dirmacs/forge) - AI pair programmer for 300+ models
- [daedra](https://github.com/dirmacs/daedra) - DuckDuckGo-powered web search MCP server
