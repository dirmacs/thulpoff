//! thulpoff-core — Core types and traits for skill distillation.
//!
//! Defines message types, tool calls, completion request/response,
//! skill generation types, and evaluation types.

use serde::{Deserialize, Serialize};

// =============================================================================
// Error types
// =============================================================================

#[derive(Debug, thiserror::Error)]
pub enum ThulpoffError {
    #[error("Provider error: {0}")]
    Provider(String),
    #[error("Generation error: {0}")]
    Generation(String),
    #[error("Evaluation error: {0}")]
    Evaluation(String),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Serialization error: {0}")]
    Serde(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, ThulpoffError>;

// =============================================================================
// Message types (LLM conversation)
// =============================================================================

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum MessageRole {
    System,
    User,
    Assistant,
    Tool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: MessageRole,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<Vec<ToolCall>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_call_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    pub id: String,
    pub name: String,
    pub arguments: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ToolDefinition {
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value,
}

// =============================================================================
// Completion request/response
// =============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
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

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TokenUsage {
    pub input_tokens: u32,
    pub output_tokens: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FinishReason {
    Stop,
    ToolUse,
    MaxTokens,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompletionResponse {
    pub content: String,
    pub tool_calls: Vec<ToolCall>,
    pub usage: TokenUsage,
    pub finish_reason: FinishReason,
}

// =============================================================================
// Provider trait
// =============================================================================

#[async_trait::async_trait]
pub trait LlmProvider: Send + Sync {
    async fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse>;
    fn name(&self) -> &str;
}

// =============================================================================
// Skill distillation types
// =============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TeacherSession {
    pub task_description: String,
    pub messages: Vec<Message>,
    pub tool_calls: Vec<ToolCall>,
    pub model: String,
    pub usage: TokenUsage,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneratedSkill {
    pub name: String,
    pub description: String,
    pub frontmatter: serde_json::Value,
    pub content: String,
    pub test_cases: Vec<TestCase>,
    pub source_session: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestCase {
    pub name: String,
    pub input: serde_json::Value,
    pub expected_behavior: String,
    pub pass_criteria: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationResult {
    pub skill_name: String,
    pub model: String,
    pub test_results: Vec<TestResult>,
    pub overall_score: f64,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestResult {
    pub test_name: String,
    pub passed: bool,
    pub score: f64,
    pub output: String,
    pub error: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn message_serde_roundtrip() {
        let msg = Message {
            role: MessageRole::User,
            content: "Hello".into(),
            tool_calls: None,
            tool_call_id: None,
        };
        let json = serde_json::to_string(&msg).unwrap();
        let parsed: Message = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.role, MessageRole::User);
        assert_eq!(parsed.content, "Hello");
    }

    #[test]
    fn tool_call_serde() {
        let tc = ToolCall {
            id: "tc-1".into(),
            name: "read_file".into(),
            arguments: serde_json::json!({"path": "/tmp/test.rs"}),
        };
        let json = serde_json::to_string(&tc).unwrap();
        let parsed: ToolCall = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.name, "read_file");
    }

    #[test]
    fn completion_request_optional_fields() {
        let json = r#"{"messages":[],"model":"claude-opus-4-6"}"#;
        let req: CompletionRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.model, "claude-opus-4-6");
        assert_eq!(req.max_tokens, None);
        assert_eq!(req.tools, None);
    }

    #[test]
    fn token_usage_defaults() {
        let usage = TokenUsage::default();
        assert_eq!(usage.input_tokens, 0);
        assert_eq!(usage.output_tokens, 0);
    }

    #[test]
    fn generated_skill_serde() {
        let skill = GeneratedSkill {
            name: "test-skill".into(),
            description: "A test".into(),
            frontmatter: serde_json::json!({"version": "1.0"}),
            content: "# Test\nDo something.".into(),
            test_cases: vec![],
            source_session: None,
        };
        let json = serde_json::to_string(&skill).unwrap();
        assert!(json.contains("test-skill"));
    }

    #[test]
    fn test_case_serde() {
        let tc = TestCase {
            name: "basic".into(),
            input: serde_json::json!({"query": "hello"}),
            expected_behavior: "should respond".into(),
            pass_criteria: vec!["non-empty response".into()],
        };
        let json = serde_json::to_value(&tc).unwrap();
        assert_eq!(json["pass_criteria"][0], "non-empty response");
    }

    #[test]
    fn evaluation_result_serde() {
        let result = EvaluationResult {
            skill_name: "test".into(),
            model: "mistral-small".into(),
            test_results: vec![],
            overall_score: 0.85,
            timestamp: chrono::Utc::now(),
        };
        let json = serde_json::to_value(&result).unwrap();
        assert_eq!(json["overall_score"], 0.85);
    }

    #[test]
    fn error_display() {
        let e = ThulpoffError::Provider("timeout".into());
        assert_eq!(format!("{}", e), "Provider error: timeout");
    }
}
