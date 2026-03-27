# thulpoff CLI Reference

## Overview

```
thulpoff - Rust implementation of skill distillation for AI agents

USAGE:
    thulpoff <COMMAND>

COMMANDS:
    generate    Generate a skill from a teacher model solving a task
    eval        Evaluate a skill with student models
    list        List generated skills
    runs        View evaluation run history
    refine      Refine a skill based on evaluation failures
    help        Print help message

OPTIONS:
    -h, --help       Print help
    -V, --version    Print version
```

---

## `thulpoff generate`

Generate a SKILL.md from teacher model demonstration.

```
USAGE:
    thulpoff generate [OPTIONS] --task <TASK>

REQUIRED:
    -t, --task <TASK>              Task description for the teacher to solve
                                   This should be a clear, specific task that the
                                   teacher model will demonstrate solving.

OPTIONS:
    -n, --name <NAME>              Skill name
                                   If not provided, auto-generated from task.
                                   Used as directory name and in SKILL.md frontmatter.

    -m, --model <MODEL>            Teacher model to use
                                   [default: claude-sonnet-4-20250514]
                                   Examples: claude-sonnet-4-20250514, gpt-4o,
                                   claude-3-5-haiku-20241022

    -p, --provider <PROVIDER>      LLM provider
                                   [default: anthropic]
                                   Options: anthropic, openai, openai-compat

    --base-url <URL>               Base URL for OpenAI-compatible providers
                                   Required when provider is openai-compat.
                                   Examples:
                                     - http://localhost:11434/v1 (Ollama)
                                     - http://localhost:8080/v1 (llama.cpp)
                                     - https://integrate.api.nvidia.com/v1 (NIM)

    --api-key <KEY>                API key (overrides environment variable)
                                   Default: $ANTHROPIC_API_KEY, $OPENAI_API_KEY,
                                   or $NVIDIA_API_KEY based on provider

    -o, --output <DIR>             Output directory for generated skill
                                   [default: ./skills]

    --test-cases <N>               Number of test cases to generate
                                   [default: 5]
                                   More test cases = better evaluation coverage
                                   but higher cost.

    --include-references           Extract reference files from teacher session
                                   Captures code snippets, templates, examples
                                   that the teacher used/generated.

    --max-turns <N>                Maximum conversation turns for teacher
                                   [default: 20]

    --temperature <TEMP>           Temperature for teacher model
                                   [default: 0.7]

    -v, --verbose                  Verbose output (show teacher conversation)

    -h, --help                     Print help
```

### Examples

```bash
# Basic generation with Claude
thulpoff generate \
  --task "Write an optimized CUDA kernel for matrix multiplication"

# Named skill with more test cases
thulpoff generate \
  --task "Write an optimized CUDA kernel for matrix multiplication" \
  --name cuda-matmul \
  --test-cases 10 \
  --include-references

# Using GPT-4o as teacher
thulpoff generate \
  --task "Implement a rate limiter in Rust using token bucket algorithm" \
  --name rust-rate-limiter \
  --provider openai \
  --model gpt-4o

# Using NVIDIA NIM
thulpoff generate \
  --task "Write a Python async web scraper with error handling" \
  --name py-scraper \
  --provider openai-compat \
  --base-url https://integrate.api.nvidia.com/v1 \
  --model meta/llama-3.1-405b-instruct
```

---

## `thulpoff eval`

Evaluate a skill with student models.

```
USAGE:
    thulpoff eval [OPTIONS] --skill <SKILL>

REQUIRED:
    -s, --skill <SKILL>            Skill name or path to skill directory
                                   Can be:
                                     - Skill name: "cuda-matmul"
                                     - Relative path: "./skills/cuda-matmul"
                                     - Absolute path: "/home/user/skills/cuda-matmul"

OPTIONS:
    -m, --model <MODEL>            Student model(s) to evaluate
                                   Can be specified multiple times.
                                   [default: claude-3-5-haiku-20241022]
                                   Examples:
                                     --model claude-3-5-haiku-20241022
                                     --model gpt-4o-mini
                                     --model qwen2.5-coder:7b

    -p, --provider <PROVIDER>      LLM provider for student models
                                   [default: anthropic]
                                   Options: anthropic, openai, openai-compat

    --base-url <URL>               Base URL for OpenAI-compatible providers

    --api-key <KEY>                API key (overrides environment variable)

    --baseline                     Run baseline comparison (without skill)
                                   Runs each test case twice: once with skill
                                   context and once without. Computes improvement
                                   metrics.

    --test-cases <IDS>             Run specific test cases only
                                   Comma-separated list of test case IDs.
                                   Default: run all test cases.

    --max-turns <N>                Maximum conversation turns per test
                                   [default: 10]

    --timeout <SECONDS>            Timeout per test case
                                   [default: 300]

    --parallel <N>                 Run N test cases in parallel
                                   [default: 1]
                                   Higher values = faster but more API cost.

    -o, --output <FILE>            Output results to file (JSON)
                                   If not specified, results are saved to
                                   runs/<skill>/<run-id>.json

    --no-save                      Don't save run to history

    -v, --verbose                  Verbose output (show model responses)

    -h, --help                     Print help
```

### Examples

```bash
# Basic evaluation with Haiku
thulpoff eval --skill cuda-matmul

# Evaluation with baseline comparison
thulpoff eval \
  --skill cuda-matmul \
  --model claude-3-5-haiku-20241022 \
  --baseline

# Multiple models
thulpoff eval \
  --skill cuda-matmul \
  --model claude-3-5-haiku-20241022 \
  --model gpt-4o-mini \
  --baseline

# Local model via Ollama
thulpoff eval \
  --skill cuda-matmul \
  --model qwen2.5-coder:32b \
  --provider openai-compat \
  --base-url http://localhost:11434/v1

# Parallel execution with output file
thulpoff eval \
  --skill cuda-matmul \
  --parallel 4 \
  --output results.json
```

---

## `thulpoff list`

List available skills.

```
USAGE:
    thulpoff list [OPTIONS]

OPTIONS:
    -d, --dir <DIR>                Skills directory
                                   [default: ./skills]

    --format <FORMAT>              Output format
                                   [default: table]
                                   Options: table, json

    --with-results                 Include latest evaluation results
                                   Shows pass rates and improvement metrics.

    --sort <FIELD>                 Sort by field
                                   [default: name]
                                   Options: name, created, updated, pass-rate

    -h, --help                     Print help
```

### Examples

```bash
# List all skills
thulpoff list

# List with evaluation results
thulpoff list --with-results

# JSON output
thulpoff list --format json

# Custom directory
thulpoff list --dir /path/to/skills
```

### Sample Output

```
┌─────────────────┬──────────────────────────────────────────┬─────────────┬────────────┐
│ Name            │ Description                              │ Created     │ Test Cases │
├─────────────────┼──────────────────────────────────────────┼─────────────┼────────────┤
│ cuda-matmul     │ Optimized CUDA matrix multiplication     │ 2026-01-29  │ 10         │
│ rust-rate-limit │ Token bucket rate limiter in Rust        │ 2026-01-28  │ 5          │
│ py-scraper      │ Async web scraper with error handling    │ 2026-01-27  │ 8          │
└─────────────────┴──────────────────────────────────────────┴─────────────┴────────────┘
```

With `--with-results`:

```
┌─────────────────┬────────────┬────────────────┬─────────────┬─────────────┐
│ Name            │ Test Cases │ Baseline Pass  │ Skill Pass  │ Improvement │
├─────────────────┼────────────┼────────────────┼─────────────┼─────────────┤
│ cuda-matmul     │ 10         │ 30%            │ 80%         │ +50%        │
│ rust-rate-limit │ 5          │ 40%            │ 100%        │ +60%        │
│ py-scraper      │ 8          │ 50%            │ 87.5%       │ +37.5%      │
└─────────────────┴────────────┴────────────────┴─────────────┴─────────────┘
```

---

## `thulpoff runs`

View evaluation run history.

```
USAGE:
    thulpoff runs [OPTIONS]

OPTIONS:
    --skill <SKILL>                Filter by skill name

    --model <MODEL>                Filter by student model

    --limit <N>                    Number of runs to show
                                   [default: 10]

    --format <FORMAT>              Output format
                                   [default: table]
                                   Options: table, json

    --run <ID>                     Show details of specific run
                                   Displays full test results and metrics.

    -h, --help                     Print help
```

### Examples

```bash
# Show recent runs
thulpoff runs

# Filter by skill
thulpoff runs --skill cuda-matmul

# Filter by model
thulpoff runs --model claude-3-5-haiku-20241022

# Show specific run details
thulpoff runs --run abc123

# JSON output
thulpoff runs --format json --limit 50
```

### Sample Output

```
┌──────────┬─────────────────┬─────────────────────────────┬─────────────┬─────────────┬─────────────┐
│ Run ID   │ Skill           │ Model                       │ Date        │ Pass Rate   │ Improvement │
├──────────┼─────────────────┼─────────────────────────────┼─────────────┼─────────────┼─────────────┤
│ abc123   │ cuda-matmul     │ claude-3-5-haiku-20241022   │ 2026-01-29  │ 80%         │ +50%        │
│ def456   │ cuda-matmul     │ gpt-4o-mini                 │ 2026-01-29  │ 70%         │ +40%        │
│ ghi789   │ rust-rate-limit │ claude-3-5-haiku-20241022   │ 2026-01-28  │ 100%        │ +60%        │
└──────────┴─────────────────┴─────────────────────────────┴─────────────┴─────────────┴─────────────┘
```

---

## `thulpoff refine`

Refine a skill based on evaluation failures.

```
USAGE:
    thulpoff refine [OPTIONS] --skill <SKILL>

REQUIRED:
    -s, --skill <SKILL>            Skill to refine

OPTIONS:
    --run <ID>                     Use failures from specific run
                                   If not specified, uses most recent run.

    -m, --model <MODEL>            Model for refinement analysis
                                   [default: claude-sonnet-4-20250514]

    -p, --provider <PROVIDER>      LLM provider
                                   [default: anthropic]

    --base-url <URL>               Base URL for OpenAI-compatible providers

    --dry-run                      Show proposed changes without applying

    --backup                       Create backup of original skill
                                   Saves to SKILL.md.bak

    -v, --verbose                  Verbose output

    -h, --help                     Print help
```

### Examples

```bash
# Refine based on most recent run
thulpoff refine --skill cuda-matmul

# Refine based on specific run
thulpoff refine --skill cuda-matmul --run abc123

# Preview changes without applying
thulpoff refine --skill cuda-matmul --dry-run

# Create backup before refining
thulpoff refine --skill cuda-matmul --backup
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `NVIDIA_API_KEY` | NVIDIA NIM API key |
| `THULPOFF_SKILLS_DIR` | Default skills directory |
| `THULPOFF_RUNS_DIR` | Default runs directory |
| `THULPOFF_DEFAULT_PROVIDER` | Default provider (anthropic, openai, openai-compat) |
| `THULPOFF_DEFAULT_TEACHER` | Default teacher model |
| `THULPOFF_DEFAULT_STUDENT` | Default student model |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Provider/API error |
| 4 | Skill not found |
| 5 | Run not found |
| 6 | Timeout |

---

## Configuration File

Optional configuration file at `~/.config/thulpoff/config.toml`:

```toml
# Default provider settings
[defaults]
provider = "anthropic"
teacher_model = "claude-sonnet-4-20250514"
student_model = "claude-3-5-haiku-20241022"
skills_dir = "./skills"
runs_dir = "./runs"

# Provider configurations
[providers.anthropic]
api_key = "${ANTHROPIC_API_KEY}"

[providers.openai]
api_key = "${OPENAI_API_KEY}"

[providers.nvidia]
api_key = "${NVIDIA_API_KEY}"
base_url = "https://integrate.api.nvidia.com/v1"

[providers.ollama]
base_url = "http://localhost:11434/v1"

# Generation settings
[generation]
default_test_cases = 5
max_turns = 20
temperature = 0.7
include_references = false

# Evaluation settings
[evaluation]
max_turns = 10
timeout = 300
parallel = 1
run_baseline = true
```
