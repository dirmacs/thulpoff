# thulpoff Architecture

## System Overview

thulpoff is designed as a modular skill distillation framework with clear separation between:
- **CLI layer** - User-facing commands
- **Engine layer** - Generation, evaluation, refinement logic
- **Provider layer** - LLM API abstractions (leveraging ares-server)
- **Storage layer** - Skill files and run persistence

### Key Design Decision: Integration with ares-server

thulpoff leverages **ares-server** as its LLM infrastructure layer, similar to how the Python 
`upskill` uses `fast-agent`. This provides:

- **LLMClient trait** - Unified interface for all LLM providers
- **ToolCallRecord** - Complete tool invocation traces (critical for distillation)
- **ToolCoordinatorResult** - Multi-turn tool calling with full execution history
- **ProviderRegistry** - Multi-model configuration and management

See [INTEGRATION.md](./INTEGRATION.md) for the full integration analysis.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              thulpoff                                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                      CLI Layer (clap v4)                            │  │
│  │   generate  |  eval  |  list  |  runs  |  refine                   │  │
│  └──────────────────────────────┬─────────────────────────────────────┘  │
│                                 │                                         │
│                                 ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        Engine Layer                                 │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │  │
│  │  │ GenerationEngine │  │ EvaluationHarness│  │ RefinementEngine │  │  │
│  │  │ - TeacherSession │  │ - TaskExecutor   │  │ - FailureAnalysis│  │  │
│  │  │ - SkillExtractor │  │ - Scorer         │  │ - SkillImprover  │  │  │
│  │  │ - TestCaseGen    │  │ - MetricsCompute │  │                  │  │  │
│  │  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │  │
│  │           │                     │                     │            │  │
│  │           └─────────────────────┼─────────────────────┘            │  │
│  └─────────────────────────────────┼──────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    Provider Adapter Layer                           │  │
│  │                                                                     │  │
│  │  ┌─────────────────────┐    ┌────────────────────────────────────┐ │  │
│  │  │   AnthropicClient   │    │      ares-server re-exports        │ │  │
│  │  │   (NEW - thulpoff)  │    │  ┌────────────┐  ┌──────────────┐  │ │  │
│  │  │                     │    │  │ LLMClient  │  │ProviderReg   │  │ │  │
│  │  │   Implements ares   │    │  │ trait      │  │istry         │  │ │  │
│  │  │   LLMClient trait   │    │  ├────────────┤  └──────────────┘  │ │  │
│  │  └─────────────────────┘    │  │OpenAIClient│                    │ │  │
│  │                             │  │OllamaClient│                    │ │  │
│  │                             │  │LlamaCpp    │                    │ │  │
│  │                             │  └────────────┘                    │ │  │
│  │                             └────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    Trace Capture Layer (from ares)                  │  │
│  │                                                                     │  │
│  │  ┌────────────────────┐  ┌──────────────────────────────────────┐  │  │
│  │  │   ToolCallRecord   │  │      ToolCoordinatorResult           │  │  │
│  │  │   - id             │  │      - content (final response)      │  │  │
│  │  │   - name           │  │      - tool_calls: Vec<Record>       │  │  │
│  │  │   - arguments      │  │      - iterations                    │  │  │
│  │  │   - result         │  │      - finish_reason                 │  │  │
│  │  │   - success        │  │                                      │  │  │
│  │  │   - duration_ms    │  │      (replaces TeacherSessionCapture)│  │  │
│  │  └────────────────────┘  └──────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                          ▼
┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│   ares-server    │    │    thulp Ecosystem   │    │       Storage        │
│   (LLM infra)    │    │                      │    │                      │
│                  │    │  ┌────────────────┐  │    │  ┌────────────────┐  │
│  - LLMClient     │    │  │thulp-skill-    │  │    │  │ skills/        │  │
│  - ToolCallRecord│    │  │files ✅        │  │    │  │   <name>/      │  │
│  - OpenAIClient  │    │  │(SKILL.md)      │  │    │  │   SKILL.md     │  │
│  - OllamaClient  │    │  └────────────────┘  │    │  │   meta.json    │  │
│  - LlamaCppClient│    │                      │    │  │   tests.json   │  │
│  - ProviderReg   │    │  ┌────────────────┐  │    │  └────────────────┘  │
│                  │    │  │thulp-skills    │  │    │                      │
└──────────────────┘    │  │(execution)     │  │    │  ┌────────────────┐  │
                        │  └────────────────┘  │    │  │ runs/          │  │
                        │                      │    │  │   <run_id>.json│  │
                        │  ┌────────────────┐  │    │  └────────────────┘  │
                        │  │thulp-guidance  │  │    │                      │
                        │  │(prompts)       │  │    └──────────────────────┘
                        │  └────────────────┘  │
                        │                      │
                        │  ┌────────────────┐  │
                        │  │thulp-workspace │  │
                        │  │(session mgmt)  │  │
                        │  └────────────────┘  │
                        │                      │
                        └──────────────────────┘
```

## Component Responsibilities

### What thulpoff Builds (Core IP)

| Component | Purpose | Notes |
|-----------|---------|-------|
| `AnthropicClient` | Claude API integration | ares lacks this |
| `GenerationEngine` | Orchestrate teacher demonstration | Core distillation logic |
| `SkillExtractor` | Analyze traces → SKILL.md | Pattern recognition |
| `TestCaseGenerator` | Generate validation tests | From task description |
| `EvaluationHarness` | Run tests, compare results | Scoring logic |
| `Scorer` | Task success determination | Domain-specific |
| `RefinementEngine` | LLM-driven improvement | Failure analysis |
| CLI | User interface | clap v4 |

### What thulpoff Reuses (from ares-server)

| Component | Source | Purpose |
|-----------|--------|---------|
| `LLMClient` trait | `ares/src/llm/client.rs` | Unified LLM interface |
| `OpenAIClient` | `ares/src/llm/openai.rs` | GPT/O-series models |
| `OllamaClient` | `ares/src/llm/ollama.rs` | Local Ollama models |
| `LlamaCppClient` | `ares/src/llm/llamacpp.rs` | llama.cpp servers |
| `ProviderRegistry` | `ares/src/llm/provider_registry.rs` | Multi-model config |
| `ToolCallRecord` | `ares/src/llm/ollama.rs` | Tool invocation traces |
| `ToolCoordinatorResult` | `ares/src/llm/ollama.rs` | Complete session trace |
| `ToolCall`, `ToolDefinition` | `ares/src/types/mod.rs` | Tool schema types |

### What thulpoff Reuses (from thulp)

| Component | Source | Purpose |
|-----------|--------|---------|
| `SkillFile` | `thulp-skill-files` | SKILL.md parsing |
| `SkillLoader` | `thulp-skill-files` | Load from directories |
| `Preprocessor` | `thulp-skill-files` | Variable interpolation |
| `Skill` | `thulp-skills` | Runtime execution |
| `PromptTemplate` | `thulp-guidance` | Prompt templates |
| `Workspace` | `thulp-workspace` | Session management |

## Directory Structure

```
thulpoff/
├── Cargo.toml
├── README.md
├── docs/
│   ├── ARCHITECTURE.md        # This file
│   ├── INTEGRATION.md         # ares/thulp integration analysis
│   ├── ROADMAP.md
│   ├── DEPENDENCIES.md
│   ├── PROVIDERS.md
│   ├── TYPES.md
│   ├── CLI.md
│   └── EXAMPLES.md
│
├── src/
│   ├── lib.rs                 # Public API, re-exports
│   ├── main.rs                # CLI entry point
│   │
│   ├── cli/
│   │   ├── mod.rs
│   │   ├── generate.rs        # `thulpoff generate` command
│   │   ├── eval.rs            # `thulpoff eval` command
│   │   ├── list.rs            # `thulpoff list` command
│   │   ├── runs.rs            # `thulpoff runs` command
│   │   └── refine.rs          # `thulpoff refine` command
│   │
│   ├── provider/
│   │   ├── mod.rs             # Re-export ares LLMClient + providers
│   │   └── anthropic.rs       # Claude API (NEW - ares lacks this)
│   │   # NOTE: OpenAI, Ollama, LlamaCpp re-exported from ares-server
│   │
│   ├── generation/
│   │   ├── mod.rs
│   │   ├── engine.rs          # GenerationEngine orchestration
│   │   ├── teacher.rs         # Teacher session using ares ToolCoordinator
│   │   ├── extractor.rs       # SkillExtractor (traces → SKILL.md)
│   │   ├── test_cases.rs      # Test case generation
│   │   └── references.rs      # Reference file extraction
│   │
│   ├── evaluation/
│   │   ├── mod.rs
│   │   ├── harness.rs         # Evaluation harness
│   │   ├── executor.rs        # Task executor (uses thulp-skills)
│   │   ├── scorer.rs          # Task success scorer
│   │   └── metrics.rs         # Baseline vs skill comparison
│   │
│   ├── refinement/
│   │   ├── mod.rs
│   │   └── refiner.rs         # LLM-driven skill refinement
│   │
│   ├── skill/
│   │   ├── mod.rs             # Re-export thulp-skill-files types
│   │   ├── writer.rs          # SKILL.md generation/writing
│   │   └── meta.rs            # skill_meta.json handling
│   │
│   ├── storage/
│   │   ├── mod.rs
│   │   ├── runs.rs            # Run persistence (JSON)
│   │   └── skills.rs          # Skill directory management
│   │
│   ├── trace/
│   │   ├── mod.rs             # Re-export ares trace types
│   │   └── adapter.rs         # Adapt ToolCoordinatorResult → TeacherSession
│   │
│   └── error.rs               # Error types (thiserror)
│
├── examples/
│   ├── cuda_kernel_skill.rs   # Example: CUDA kernel generation skill
│   └── bash_tools_skill.rs    # Example: Bash command skill
│
└── tests/
    ├── integration/
    │   ├── generate_test.rs
    │   └── eval_test.rs
    └── unit/
        └── ...
```

## Component Details

### 1. CLI Layer (`src/cli/`)

The CLI is built with `clap v4` using derive macros for type-safe argument parsing.

```rust
#[derive(Parser)]
#[command(name = "thulpoff")]
#[command(about = "Rust implementation of skill distillation for AI agents")]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    Generate(GenerateArgs),
    Eval(EvalArgs),
    List(ListArgs),
    Runs(RunsArgs),
    Refine(RefineArgs),
}
```

### 2. Provider Layer (`src/provider/`)

The provider layer re-exports ares-server's `LLMClient` trait and implementations,
adding only the missing Anthropic support:

```rust
// Re-export ares types
pub use ares::llm::{
    LLMClient, LLMResponse, 
    OpenAIClient, OllamaClient, LlamaCppClient,
    ProviderRegistry, ConfigBasedLLMFactory,
};
pub use ares::types::{ToolCall, ToolDefinition, ToolResult};

// thulpoff's own Anthropic implementation
mod anthropic;
pub use anthropic::AnthropicClient;
```

The `AnthropicClient` implements ares's `LLMClient` trait:

```rust
pub struct AnthropicClient {
    client: reqwest::Client,
    api_key: String,
    model: String,
    base_url: String,
}

#[async_trait]
impl LLMClient for AnthropicClient {
    async fn generate(&self, prompt: &str) -> Result<String>;
    async fn generate_with_system(&self, system: &str, prompt: &str) -> Result<String>;
    async fn generate_with_history(&self, messages: &[(String, String)]) -> Result<String>;
    async fn generate_with_tools(&self, prompt: &str, tools: &[ToolDefinition]) -> Result<LLMResponse>;
    fn model_name(&self) -> &str { &self.model }
}
```

Provider availability:
- **AnthropicClient** - Direct Claude API (Messages API) - **NEW in thulpoff**
- **OpenAIClient** - OpenAI API (Chat Completions) - from ares
- **OllamaClient** - Ollama API with tool coordination - from ares
- **LlamaCppClient** - llama.cpp servers - from ares

### 3. Generation Engine (`src/generation/`)

The generation engine orchestrates the teacher demonstration, leveraging ares-server's
trace capture capabilities:

1. **Teacher Session** - Uses ares `OllamaToolCoordinator` or equivalent for multi-turn 
   tool-calling conversations that produce `ToolCoordinatorResult`
2. **Skill Extraction** - Analyze the `Vec<ToolCallRecord>` to extract reusable patterns
3. **Test Case Generation** - Create test cases that validate the skill
4. **Reference Extraction** - Pull out code snippets and templates

```rust
use ares::llm::{LLMClient, ToolCoordinatorResult, ToolCallRecord};
use thulp_skill_files::{SkillFile, SkillFrontmatter};

pub struct GenerationEngine {
    provider: Arc<dyn LLMClient>,
    config: GenerationConfig,
}

impl GenerationEngine {
    pub async fn generate(&self, task: &str) -> Result<GeneratedSkill> {
        // 1. Run teacher session (returns ares ToolCoordinatorResult)
        let trace = self.run_teacher_session(task).await?;
        
        // 2. Extract skill from tool call trace
        let skill_content = self.extract_skill(&trace.tool_calls).await?;
        
        // 3. Generate test cases
        let test_cases = self.generate_test_cases(task, &skill_content).await?;
        
        // 4. Extract references from tool results
        let references = self.extract_references(&trace.tool_calls).await?;
        
        Ok(GeneratedSkill {
            skill_file: SkillFile { ... },
            test_cases,
            references,
            // Include trace for debugging/analysis
            teacher_trace: trace,
        })
    }
    
    async fn run_teacher_session(&self, task: &str) -> Result<ToolCoordinatorResult> {
        // Uses ares tool coordination to capture complete execution trace
        // Each tool call is recorded with: id, name, arguments, result, success, duration_ms
    }
}
```

The key insight is that `ToolCoordinatorResult` from ares already captures everything
needed for skill distillation:
- `content` - The teacher's final response
- `tool_calls: Vec<ToolCallRecord>` - Complete trace of every tool invocation
- `iterations` - Number of turns in the conversation
- `finish_reason` - Why the conversation ended
```

### 4. Evaluation Harness (`src/evaluation/`)

The evaluation harness runs test cases with and without skill context,
using thulp-skills for execution:

```rust
use ares::llm::{LLMClient, ToolCoordinatorResult};
use thulp_skill_files::SkillFile;
use thulp_skills::SkillExecutor;

pub struct EvaluationHarness {
    provider: Arc<dyn LLMClient>,
    executor: SkillExecutor,  // From thulp-skills
    scorer: Scorer,
}

impl EvaluationHarness {
    pub async fn evaluate(
        &self,
        skill: &SkillFile,
        test_cases: &[TestCase],
        run_baseline: bool,
    ) -> Result<EvalRun> {
        let mut baseline_results = Vec::new();
        let mut skill_results = Vec::new();
        
        for test_case in test_cases {
            // Run with skill (skill content injected as system prompt)
            let skill_trace = self.run_with_skill(skill, test_case).await?;
            let skill_score = self.scorer.score(&skill_trace, &test_case.expected)?;
            skill_results.push(TestResult { trace: skill_trace, score: skill_score });
            
            // Run baseline (no skill) if requested
            if run_baseline {
                let baseline_trace = self.run_without_skill(test_case).await?;
                let baseline_score = self.scorer.score(&baseline_trace, &test_case.expected)?;
                baseline_results.push(TestResult { trace: baseline_trace, score: baseline_score });
            }
        }
        
        // Compute summary metrics (skill improvement over baseline)
        let summary = self.compute_summary(&baseline_results, &skill_results);
        
        Ok(EvalRun { 
            baseline_results,
            skill_results,
            summary,
            // Include all traces for analysis
        })
    }
}
```

### 5. Refinement Engine (`src/refinement/`)

Uses LLM to analyze failures and improve the skill:

```rust
use ares::llm::LLMClient;
use thulp_skill_files::SkillFile;
use thulp_guidance::PromptTemplate;

pub struct RefinementEngine {
    provider: Arc<dyn LLMClient>,
    refinement_template: PromptTemplate,  // From thulp-guidance
}

impl RefinementEngine {
    pub async fn refine(
        &self,
        skill: &SkillFile,
        failures: &[TestResult],
    ) -> Result<SkillFile> {
        // Build prompt showing failures and asking for improvements
        let prompt = self.refinement_template.render(&RefinementContext {
            skill_content: &skill.content,
            failures: failures.iter().map(|f| FailureInfo {
                test_case: &f.test_case,
                actual_output: &f.trace.content,
                expected: &f.expected,
                tool_calls: &f.trace.tool_calls,
            }).collect(),
        })?;
        
        let response = self.provider.generate(&prompt).await?;
        let improved_content = self.parse_improved_skill(&response)?;
        
        Ok(SkillFile {
            content: improved_content,
            ..skill.clone()
        })
    }
}
```

### 6. Storage Layer (`src/storage/`)

Manages skill files and evaluation run history:

```rust
pub struct SkillStorage {
    base_dir: PathBuf,
}

impl SkillStorage {
    pub fn save_skill(&self, skill: &GeneratedSkill) -> Result<PathBuf>;
    pub fn load_skill(&self, name: &str) -> Result<SkillFile>;
    pub fn list_skills(&self) -> Result<Vec<SkillInfo>>;
}

pub struct RunStorage {
    base_dir: PathBuf,
}

impl RunStorage {
    pub fn save_run(&self, run: &EvalRun) -> Result<()>;
    pub fn load_run(&self, id: &str) -> Result<EvalRun>;
    pub fn list_runs(&self, filter: RunFilter) -> Result<Vec<EvalRunSummary>>;
}
```

## Output Structure

Skills are stored in a standard directory structure:

```
skills/
└── cuda-matmul/
    ├── SKILL.md              # The generated skill
    ├── skill_meta.json       # Metadata + eval results
    ├── test_cases.json       # Generated test cases
    └── references/           # Optional reference files
        └── kernel_template.cu
```

## Integration with ares-server and thulp

thulpoff integrates deeply with both ares-server (LLM infrastructure) and the thulp 
ecosystem (skill management). See [INTEGRATION.md](./INTEGRATION.md) for full analysis.

### ares-server Integration (LLM Infrastructure)

```toml
# Cargo.toml
[dependencies]
ares = { path = "../ares" }
```

Re-exported from ares:
- `LLMClient` trait - Unified LLM interface
- `OpenAIClient`, `OllamaClient`, `LlamaCppClient` - Provider implementations
- `ProviderRegistry` - Multi-model configuration
- `ToolCallRecord`, `ToolCoordinatorResult` - Trace capture (critical for distillation)
- `ToolCall`, `ToolDefinition`, `ToolResult` - Tool schema types

### thulp Ecosystem Integration

```toml
# Cargo.toml
[dependencies]
thulp-skill-files = { workspace = true }  # SKILL.md parsing (Phase 0 - DONE)
thulp-skills = { workspace = true }       # Skill execution
thulp-guidance = { workspace = true }     # Prompt templates
thulp-workspace = { workspace = true }    # Session management
```

1. **thulp-skill-files** (required, completed)
   - Provides `SkillFile` struct for SKILL.md parsing
   - Handles frontmatter, content, and variable interpolation
   - thulpoff uses for reading and writing skill files

2. **thulp-skills** (required)
   - Provides `Skill` and `SkillExecutor` for runtime execution
   - Used by EvaluationHarness to run skills in controlled environment

3. **thulp-guidance** (recommended)
   - Provides `PromptTemplate` for generation/evaluation prompts
   - Used by RefinementEngine for structured prompt building

4. **thulp-workspace** (optional)
   - Load skills from project/personal/enterprise directories
   - Discovery by intent matching
   - Session/run management

5. **thulp-registry** (optional)
   - Register generated skills in a `SkillRegistry`
   - Enable skill marketplace integration

6. **lancor** (optional)
   - Provides optimized client for llama.cpp servers
   - Alternative to ares LlamaCppClient for performance-critical use

## Data Flow

### Generation Flow

```
User Task
    │
    ▼
┌─────────────────┐
│ Teacher Model   │  (e.g., Claude Sonnet)
│ Demonstration   │
└────────┬────────┘
         │ Multi-turn conversation
         ▼
┌─────────────────┐
│ Skill Extractor │
└────────┬────────┘
         │ Analyze patterns
         ▼
┌─────────────────┐     ┌──────────────────┐
│ SKILL.md Writer │────▶│ skills/name/     │
└─────────────────┘     │   SKILL.md       │
         │              │   test_cases.json│
         ▼              │   skill_meta.json│
┌─────────────────┐     └──────────────────┘
│ Test Case Gen   │
└─────────────────┘
```

### Evaluation Flow

```
Skill + Test Cases
    │
    ▼
┌─────────────────────────────────────┐
│        Evaluation Harness           │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ With Skill  │  │  Baseline   │   │
│  │   Run       │  │   Run       │   │
│  └──────┬──────┘  └──────┬──────┘   │
│         │                │          │
│         ▼                ▼          │
│  ┌─────────────────────────────┐    │
│  │         Scorer              │    │
│  └─────────────────────────────┘    │
└─────────────────┬───────────────────┘
                  │
                  ▼
           ┌─────────────┐
           │ EvalRun     │
           │ (metrics)   │
           └─────────────┘
```

## Concurrency Model

- **Async runtime**: Tokio with multi-threaded runtime
- **Provider requests**: Concurrent with configurable rate limiting
- **Test case execution**: Parallel with `--parallel N` flag
- **Skill operations**: Single-threaded (file I/O is fast)

## Error Handling

All errors use `thiserror` for structured error types:

```rust
#[derive(Debug, Error)]
pub enum ThulpoffError {
    #[error("Provider error: {0}")]
    Provider(#[from] ProviderError),
    
    #[error("Generation error: {0}")]
    Generation(String),
    
    #[error("Evaluation error: {0}")]
    Evaluation(String),
    
    #[error("Skill file error: {0}")]
    SkillFile(#[from] thulp_skill_files::SkillFileError),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}
```

## Configuration

Configuration via:
1. CLI arguments (highest priority)
2. Environment variables (`THULPOFF_*`)
3. Config file (`~/.config/thulpoff/config.toml`)

```toml
# ~/.config/thulpoff/config.toml

# thulpoff-specific Anthropic config (teacher model)
[providers.anthropic]
api_key = "${ANTHROPIC_API_KEY}"
default_model = "claude-sonnet-4-20250514"

# ares-server provider configs (student models)
# These can also be configured in ares config and referenced
[providers.openai]
api_key = "${OPENAI_API_KEY}"
default_model = "gpt-4o"

[providers.nvidia]
api_key = "${NVIDIA_API_KEY}"
base_url = "https://integrate.api.nvidia.com/v1"

[providers.ollama]
base_url = "http://localhost:11434/v1"
default_model = "qwen2.5-coder:32b"

[storage]
skills_dir = "./skills"
runs_dir = "./runs"

# ares-server configuration path (optional)
# If set, thulpoff will load provider configs from ares
[ares]
config_path = "~/.config/ares/config.toml"
```

## Dependency Chain

```
thulpoff
├── ares-server                    # LLM infrastructure
│   ├── LLMClient trait
│   ├── OpenAI/Ollama/LlamaCpp clients
│   ├── ToolCallRecord (trace capture)
│   └── ProviderRegistry
│
├── thulp-skill-files ✅ (Phase 0) # SKILL.md parsing
│   ├── SkillFile
│   ├── SkillFrontmatter
│   └── SkillLoader
│
├── thulp-skills                   # Skill execution
│   ├── Skill
│   └── SkillExecutor
│
├── thulp-guidance                 # Prompt templates
│   └── PromptTemplate
│
└── thulp-workspace                # Session management
    └── Workspace
```
