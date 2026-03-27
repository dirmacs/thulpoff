# thulpoff Core Types

This document defines all core data types used in thulpoff.

## Provider Types

### Message

```rust
/// Message in a conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: MessageRole,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<Vec<ToolCall>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_call_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum MessageRole {
    System,
    User,
    Assistant,
    Tool,
}
```

### ToolCall

```rust
/// Tool call from an LLM response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    pub id: String,
    pub name: String,
    pub arguments: serde_json::Value,
}

/// Tool definition for LLM
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolDefinition {
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value,  // JSON Schema
}
```

### CompletionRequest / CompletionResponse

```rust
/// Request to an LLM provider
#[derive(Debug, Clone)]
pub struct CompletionRequest {
    pub messages: Vec<Message>,
    pub model: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<Vec<ToolDefinition>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stop: Option<Vec<String>>,
}

/// Response from an LLM provider
#[derive(Debug, Clone)]
pub struct CompletionResponse {
    pub content: String,
    pub tool_calls: Vec<ToolCall>,
    pub usage: TokenUsage,
    pub finish_reason: FinishReason,
}

/// Token usage tracking
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TokenUsage {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FinishReason {
    Stop,
    Length,
    ToolCalls,
    ContentFilter,
    Error,
}
```

### LlmProvider Trait

```rust
/// LLM provider trait (teacher/student model abstraction)
#[async_trait]
pub trait LlmProvider: Send + Sync {
    /// Get the provider name (anthropic, openai, openai-compat)
    fn name(&self) -> &str;
    
    /// Get the provider's default model
    fn default_model(&self) -> &str;
    
    /// Send a completion request
    async fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse>;
    
    /// Check if the provider supports tool calling
    fn supports_tools(&self) -> bool;
    
    /// List available models (optional)
    async fn list_models(&self) -> Result<Vec<String>> {
        Ok(vec![self.default_model().to_string()])
    }
}
```

---

## Skill Types

### SkillFile

```rust
/// Skill file structure (mirrors Claude Code format)
/// This wraps thulp-skill-files::SkillFile when available
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillFile {
    /// Skill name (from frontmatter or filename)
    pub name: String,
    
    /// Short description
    pub description: String,
    
    /// Full skill content (markdown)
    pub content: String,
    
    /// Optional frontmatter fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub frontmatter: Option<SkillFrontmatter>,
}

/// SKILL.md frontmatter (YAML)
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SkillFrontmatter {
    pub name: String,
    
    pub description: String,
    
    /// Allowed tools for this skill
    #[serde(skip_serializing_if = "Option::is_none")]
    pub allowed_tools: Option<Vec<String>>,
    
    /// Whether this skill can be invoked by the model
    #[serde(default)]
    pub disable_model_invocation: bool,
    
    /// Whether user can invoke this skill directly
    #[serde(default = "default_true")]
    pub user_invocable: bool,
    
    /// Whether approval is required before execution
    #[serde(default)]
    pub requires_approval: bool,
}

fn default_true() -> bool { true }
```

### ReferenceFile

```rust
/// Reference file embedded in skill
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReferenceFile {
    /// Relative path within references/ directory
    pub path: String,
    
    /// File content
    pub content: String,
    
    /// Optional description
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}
```

### SkillMeta

```rust
/// Skill metadata (skill_meta.json)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillMeta {
    /// Skill name (matches directory name)
    pub name: String,
    
    /// Short description
    pub description: String,
    
    /// Creation timestamp
    pub created_at: chrono::DateTime<chrono::Utc>,
    
    /// Last modification timestamp
    pub updated_at: chrono::DateTime<chrono::Utc>,
    
    /// Teacher model used for generation
    pub teacher_model: String,
    
    /// Original task used for generation
    pub generation_task: String,
    
    /// Number of test cases
    pub test_cases_count: usize,
    
    /// Latest evaluation results
    #[serde(skip_serializing_if = "Option::is_none")]
    pub latest_eval: Option<EvalSummary>,
    
    /// All evaluation run IDs
    #[serde(default)]
    pub eval_run_ids: Vec<String>,
}
```

### GeneratedSkill

```rust
/// Complete generated skill (output of generation engine)
#[derive(Debug, Clone)]
pub struct GeneratedSkill {
    /// The skill file
    pub skill_file: SkillFile,
    
    /// Generated test cases
    pub test_cases: Vec<TestCase>,
    
    /// Extracted reference files
    pub references: Vec<ReferenceFile>,
    
    /// Metadata
    pub meta: SkillMeta,
    
    /// Generation statistics
    pub generation_stats: GenerationStats,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerationStats {
    /// Total tokens used
    pub total_tokens: u32,
    
    /// Number of conversation turns
    pub turns: usize,
    
    /// Generation duration in milliseconds
    pub duration_ms: u64,
}
```

---

## Evaluation Types

### TestCase

```rust
/// Test case for skill evaluation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestCase {
    /// Unique identifier
    pub id: String,
    
    /// Test case prompt (task for the model)
    pub prompt: String,
    
    /// Expected behavior description
    pub expected_behavior: String,
    
    /// Optional validation script (bash/python)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub validation_script: Option<String>,
    
    /// Expected outputs or patterns
    #[serde(default)]
    pub expected_outputs: Vec<String>,
    
    /// Tags for categorization
    #[serde(default)]
    pub tags: Vec<String>,
    
    /// Difficulty level
    #[serde(skip_serializing_if = "Option::is_none")]
    pub difficulty: Option<Difficulty>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Difficulty {
    Easy,
    Medium,
    Hard,
}
```

### TestResult

```rust
/// Result of a single test case execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestResult {
    /// Test case ID
    pub test_case_id: String,
    
    /// Whether the test passed
    pub success: bool,
    
    /// Score (0.0 to 1.0)
    pub score: f64,
    
    /// Model output
    pub output: String,
    
    /// Conversation history
    pub messages: Vec<Message>,
    
    /// Error message if failed
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    
    /// Tokens used
    pub tokens_used: u32,
    
    /// Duration in milliseconds
    pub duration_ms: u64,
    
    /// Number of turns taken
    pub turns: usize,
    
    /// Scorer's explanation
    #[serde(skip_serializing_if = "Option::is_none")]
    pub scorer_explanation: Option<String>,
}
```

### EvalRun

```rust
/// Evaluation run record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvalRun {
    /// Unique run ID
    pub id: String,
    
    /// Skill name
    pub skill_name: String,
    
    /// Student model evaluated
    pub student_model: String,
    
    /// Provider used
    pub provider: String,
    
    /// Start timestamp
    pub started_at: chrono::DateTime<chrono::Utc>,
    
    /// End timestamp
    #[serde(skip_serializing_if = "Option::is_none")]
    pub completed_at: Option<chrono::DateTime<chrono::Utc>>,
    
    /// Run status
    pub status: RunStatus,
    
    /// Results with skill context
    pub skill_results: Vec<TestResult>,
    
    /// Results without skill (baseline)
    #[serde(default)]
    pub baseline_results: Vec<TestResult>,
    
    /// Summary metrics
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<EvalSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum RunStatus {
    Running,
    Completed,
    Failed,
    Cancelled,
}
```

### EvalSummary

```rust
/// Summary of evaluation run
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvalSummary {
    /// Total test cases
    pub total_tests: usize,
    
    /// Baseline pass count
    pub baseline_passed: usize,
    
    /// Skill pass count
    pub skill_passed: usize,
    
    /// Baseline pass rate (0.0 to 1.0)
    pub baseline_pass_rate: f64,
    
    /// Skill pass rate (0.0 to 1.0)
    pub skill_pass_rate: f64,
    
    /// Improvement (skill_pass_rate - baseline_pass_rate)
    pub improvement: f64,
    
    /// Average baseline score
    pub avg_baseline_score: f64,
    
    /// Average skill score
    pub avg_skill_score: f64,
    
    /// Average tokens used (baseline)
    pub avg_baseline_tokens: f64,
    
    /// Average tokens used (with skill)
    pub avg_skill_tokens: f64,
    
    /// Token reduction percentage
    pub token_reduction_pct: f64,
    
    /// Average duration (baseline)
    pub avg_baseline_duration_ms: f64,
    
    /// Average duration (with skill)
    pub avg_skill_duration_ms: f64,
}
```

---

## Configuration Types

### GenerationConfig

```rust
/// Configuration for skill generation
#[derive(Debug, Clone)]
pub struct GenerationConfig {
    /// Task description
    pub task: String,
    
    /// Skill name (optional, auto-generated if not provided)
    pub name: Option<String>,
    
    /// Teacher model
    pub model: String,
    
    /// Number of test cases to generate
    pub test_cases: usize,
    
    /// Whether to extract reference files
    pub include_references: bool,
    
    /// Maximum conversation turns
    pub max_turns: usize,
    
    /// Temperature for generation
    pub temperature: f32,
    
    /// Output directory
    pub output_dir: PathBuf,
}
```

### EvaluationConfig

```rust
/// Configuration for skill evaluation
#[derive(Debug, Clone)]
pub struct EvaluationConfig {
    /// Skill name or path
    pub skill: String,
    
    /// Student model
    pub model: String,
    
    /// Whether to run baseline comparison
    pub run_baseline: bool,
    
    /// Specific test case IDs to run
    pub test_case_ids: Option<Vec<String>>,
    
    /// Maximum conversation turns
    pub max_turns: usize,
    
    /// Timeout per test case in seconds
    pub timeout: u64,
    
    /// Number of parallel test cases
    pub parallel: usize,
    
    /// Output file for results
    pub output_file: Option<PathBuf>,
    
    /// Whether to save run to history
    pub save_run: bool,
}
```

### ProviderConfig

```rust
/// Provider configuration
#[derive(Debug, Clone)]
pub struct ProviderConfig {
    /// Provider type
    pub provider_type: ProviderType,
    
    /// API key
    pub api_key: Option<String>,
    
    /// Base URL (for OpenAI-compatible providers)
    pub base_url: Option<String>,
    
    /// Default model
    pub default_model: Option<String>,
    
    /// Request timeout in seconds
    pub timeout: u64,
    
    /// Max retries on failure
    pub max_retries: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProviderType {
    Anthropic,
    OpenAI,
    OpenAICompat,
}
```

---

## Error Types

```rust
use thiserror::Error;

pub type Result<T> = std::result::Result<T, ThulpoffError>;

#[derive(Debug, Error)]
pub enum ThulpoffError {
    #[error("Provider error: {message}")]
    Provider {
        message: String,
        #[source]
        source: Option<Box<dyn std::error::Error + Send + Sync>>,
    },
    
    #[error("Generation error: {0}")]
    Generation(String),
    
    #[error("Evaluation error: {0}")]
    Evaluation(String),
    
    #[error("Refinement error: {0}")]
    Refinement(String),
    
    #[error("Skill not found: {0}")]
    SkillNotFound(String),
    
    #[error("Run not found: {0}")]
    RunNotFound(String),
    
    #[error("Invalid skill file: {0}")]
    InvalidSkillFile(String),
    
    #[error("Configuration error: {0}")]
    Config(String),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    
    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    
    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),
    
    #[error("Timeout after {0} seconds")]
    Timeout(u64),
    
    #[error("Rate limited: retry after {retry_after_secs} seconds")]
    RateLimited { retry_after_secs: u64 },
    
    #[error("API error ({status}): {message}")]
    ApiError {
        status: u16,
        message: String,
    },
}
```

---

## Serialization Notes

All types use:
- `serde` for JSON/YAML serialization
- `chrono` for timestamps with UTC timezone
- `uuid` for unique IDs (v4)
- `#[serde(skip_serializing_if = "Option::is_none")]` for optional fields
- `#[serde(default)]` for fields with sensible defaults
