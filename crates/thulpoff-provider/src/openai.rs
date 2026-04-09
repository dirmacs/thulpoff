//! OpenAI-compatible provider — works with OpenAI, Ollama, llama.cpp, vLLM, etc.
//!
//! Any endpoint that implements the OpenAI chat completions API can be used.
//! Set `base_url` to target local or custom endpoints.

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use thulpoff_core::{
    CompletionRequest, CompletionResponse, FinishReason, LlmProvider, Result, ThulpoffError,
    TokenUsage, ToolCall,
};

const OPENAI_API_URL: &str = "https://api.openai.com/v1/chat/completions";
const OLLAMA_API_URL: &str = "http://localhost:11434/v1/chat/completions";

/// OpenAI-compatible provider for any endpoint implementing the chat completions API.
///
/// Works with: OpenAI, Ollama, llama.cpp, vLLM, LM Studio, etc.
pub struct OpenAiProvider {
    client: reqwest::Client,
    api_key: String,
    base_url: String,
    provider_name: String,
}

impl OpenAiProvider {
    /// Create a provider pointing at the official OpenAI API.
    pub fn new(api_key: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key,
            base_url: OPENAI_API_URL.to_string(),
            provider_name: "openai".to_string(),
        }
    }

    /// Create a provider for any OpenAI-compatible endpoint.
    pub fn with_base_url(api_key: String, base_url: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key,
            base_url,
            provider_name: "openai-compatible".to_string(),
        }
    }

    /// Create a provider for Ollama (localhost:11434).
    pub fn ollama() -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key: "ollama".to_string(),
            base_url: OLLAMA_API_URL.to_string(),
            provider_name: "ollama".to_string(),
        }
    }

    /// Create from environment variables.
    /// Checks OPENAI_API_KEY, then GENERIC_API_KEY, then falls back to "local".
    pub fn from_env() -> Result<Self> {
        let key = std::env::var("OPENAI_API_KEY")
            .or_else(|_| std::env::var("GENERIC_API_KEY"))
            .unwrap_or_else(|_| "local".to_string());

        let base_url = std::env::var("OPENAI_API_BASE")
            .or_else(|_| std::env::var("GENERIC_BASE_URL"))
            .unwrap_or_else(|_| OPENAI_API_URL.to_string());

        Ok(Self::with_base_url(key, base_url))
    }

    /// Override the display name for this provider.
    pub fn with_name(mut self, name: impl Into<String>) -> Self {
        self.provider_name = name.into();
        self
    }
}

#[derive(Serialize)]
struct OaiRequest {
    model: String,
    messages: Vec<OaiMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_tokens: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    tools: Option<Vec<OaiTool>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stop: Option<Vec<String>>,
}

#[derive(Serialize)]
struct OaiMessage {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct OaiTool {
    #[serde(rename = "type")]
    tool_type: String,
    function: OaiFunction,
}

#[derive(Serialize)]
struct OaiFunction {
    name: String,
    description: String,
    parameters: serde_json::Value,
}

#[derive(Deserialize)]
struct OaiResponse {
    choices: Vec<OaiChoice>,
    usage: Option<OaiUsage>,
}

#[derive(Deserialize)]
struct OaiChoice {
    message: OaiResponseMessage,
    finish_reason: Option<String>,
}

#[derive(Deserialize)]
struct OaiResponseMessage {
    content: Option<String>,
    tool_calls: Option<Vec<OaiToolCall>>,
}

#[derive(Deserialize)]
struct OaiToolCall {
    id: String,
    function: OaiFunctionCall,
}

#[derive(Deserialize)]
struct OaiFunctionCall {
    name: String,
    arguments: String,
}

#[derive(Deserialize)]
struct OaiUsage {
    prompt_tokens: u32,
    completion_tokens: u32,
}

#[async_trait]
impl LlmProvider for OpenAiProvider {
    async fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse> {
        let messages: Vec<OaiMessage> = request
            .messages
            .iter()
            .map(|m| OaiMessage {
                role: match m.role {
                    thulpoff_core::MessageRole::System => "system".into(),
                    thulpoff_core::MessageRole::User => "user".into(),
                    thulpoff_core::MessageRole::Assistant => "assistant".into(),
                    thulpoff_core::MessageRole::Tool => "tool".into(),
                },
                content: m.content.clone(),
            })
            .collect();

        let tools = request.tools.map(|ts| {
            ts.into_iter()
                .map(|t| OaiTool {
                    tool_type: "function".into(),
                    function: OaiFunction {
                        name: t.name,
                        description: t.description,
                        parameters: t.parameters,
                    },
                })
                .collect()
        });

        let body = OaiRequest {
            model: request.model,
            messages,
            max_tokens: request.max_tokens,
            temperature: request.temperature,
            tools,
            stop: request.stop,
        };

        let resp = self
            .client
            .post(&self.base_url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await
            .map_err(|e| ThulpoffError::Provider(format!("HTTP error: {}", e)))?;

        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            return Err(ThulpoffError::Provider(format!(
                "OpenAI-compatible API {}: {}",
                status, body
            )));
        }

        let api_resp: OaiResponse = resp
            .json()
            .await
            .map_err(|e| ThulpoffError::Provider(format!("Parse error: {}", e)))?;

        let choice = api_resp
            .choices
            .into_iter()
            .next()
            .ok_or_else(|| ThulpoffError::Provider("No choices returned".into()))?;

        let content = choice.message.content.unwrap_or_default();

        let tool_calls = choice
            .message
            .tool_calls
            .unwrap_or_default()
            .into_iter()
            .map(|tc| {
                let args = serde_json::from_str(&tc.function.arguments)
                    .unwrap_or(serde_json::Value::Object(Default::default()));
                ToolCall {
                    id: tc.id,
                    name: tc.function.name,
                    arguments: args,
                }
            })
            .collect();

        let finish_reason = match choice.finish_reason.as_deref() {
            Some("stop") => FinishReason::Stop,
            Some("tool_calls") => FinishReason::ToolUse,
            Some("length") => FinishReason::MaxTokens,
            _ => FinishReason::Stop,
        };

        let usage = api_resp
            .usage
            .map(|u| TokenUsage {
                input_tokens: u.prompt_tokens,
                output_tokens: u.completion_tokens,
            })
            .unwrap_or_default();

        Ok(CompletionResponse {
            content,
            tool_calls,
            usage,
            finish_reason,
        })
    }

    fn name(&self) -> &str {
        &self.provider_name
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn openai_request_serialization() {
        let req = OaiRequest {
            model: "gpt-4o-mini".into(),
            messages: vec![OaiMessage {
                role: "user".into(),
                content: "Hello".into(),
            }],
            max_tokens: Some(1024),
            temperature: Some(0.7),
            tools: None,
            stop: None,
        };
        let json = serde_json::to_value(&req).unwrap();
        assert_eq!(json["model"], "gpt-4o-mini");
        assert!(json.get("tools").is_none());
    }

    #[test]
    fn openai_response_deserialization() {
        let json = r#"{
            "choices": [{
                "message": {
                    "content": "Hello!",
                    "tool_calls": null
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3}
        }"#;
        let resp: OaiResponse = serde_json::from_str(json).unwrap();
        assert_eq!(resp.choices[0].message.content.as_deref(), Some("Hello!"));
        assert_eq!(resp.usage.unwrap().completion_tokens, 3);
    }

    #[test]
    fn openai_response_with_tool_calls() {
        let json = r#"{
            "choices": [{
                "message": {
                    "content": null,
                    "tool_calls": [{
                        "id": "call_abc",
                        "type": "function",
                        "function": {
                            "name": "search",
                            "arguments": "{\"query\": \"rust\"}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20}
        }"#;
        let resp: OaiResponse = serde_json::from_str(json).unwrap();
        let tc = resp.choices[0].message.tool_calls.as_ref().unwrap();
        assert_eq!(tc[0].function.name, "search");
        assert_eq!(tc[0].id, "call_abc");
    }

    #[test]
    fn openai_provider_name() {
        let p = OpenAiProvider::new("sk-test".into());
        assert_eq!(p.name(), "openai");
    }

    #[test]
    fn ollama_provider() {
        let p = OpenAiProvider::ollama();
        assert_eq!(p.name(), "ollama");
        assert!(p.base_url.contains("11434"));
        assert_eq!(p.api_key, "ollama");
    }

    #[test]
    fn custom_base_url_provider() {
        let p = OpenAiProvider::with_base_url("key".into(), "http://localhost:8080/v1/chat/completions".into());
        assert_eq!(p.name(), "openai-compatible");
        assert_eq!(p.base_url, "http://localhost:8080/v1/chat/completions");
    }

    #[test]
    fn with_name_override() {
        let p = OpenAiProvider::ollama().with_name("my-local-model");
        assert_eq!(p.name(), "my-local-model");
    }

    #[test]
    fn from_env_defaults() {
        // Without env vars set, should use defaults
        if std::env::var("OPENAI_API_KEY").is_err() && std::env::var("GENERIC_API_KEY").is_err() {
            let p = OpenAiProvider::from_env().unwrap();
            assert_eq!(p.api_key, "local");
        }
    }
}
