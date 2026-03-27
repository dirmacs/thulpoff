use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use thulpoff_core::{
    CompletionRequest, CompletionResponse, FinishReason, LlmProvider, Result, ThulpoffError,
    TokenUsage, ToolCall,
};

const ANTHROPIC_API_URL: &str = "https://api.anthropic.com/v1/messages";
const ANTHROPIC_VERSION: &str = "2023-06-01";

pub struct AnthropicProvider {
    client: reqwest::Client,
    api_key: String,
}

impl AnthropicProvider {
    pub fn new(api_key: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key,
        }
    }

    pub fn from_env() -> Result<Self> {
        let key = std::env::var("ANTHROPIC_API_KEY")
            .map_err(|_| ThulpoffError::Provider("ANTHROPIC_API_KEY not set".into()))?;
        Ok(Self::new(key))
    }
}

// Anthropic Messages API request/response types

#[derive(Serialize)]
struct AnthropicRequest {
    model: String,
    messages: Vec<AnthropicMessage>,
    max_tokens: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    system: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    tools: Option<Vec<AnthropicTool>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stop_sequences: Option<Vec<String>>,
}

#[derive(Serialize)]
struct AnthropicMessage {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct AnthropicTool {
    name: String,
    description: String,
    input_schema: serde_json::Value,
}

#[derive(Deserialize)]
struct AnthropicResponse {
    content: Vec<ContentBlock>,
    usage: AnthropicUsage,
    stop_reason: Option<String>,
}

#[derive(Deserialize)]
#[serde(tag = "type")]
enum ContentBlock {
    #[serde(rename = "text")]
    Text { text: String },
    #[serde(rename = "tool_use")]
    ToolUse {
        id: String,
        name: String,
        input: serde_json::Value,
    },
}

#[derive(Deserialize)]
struct AnthropicUsage {
    input_tokens: u32,
    output_tokens: u32,
}

#[async_trait]
impl LlmProvider for AnthropicProvider {
    async fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse> {
        let mut system = None;
        let mut messages = Vec::new();

        for msg in &request.messages {
            let role_str = match msg.role {
                thulpoff_core::MessageRole::System => {
                    system = Some(msg.content.clone());
                    continue;
                }
                thulpoff_core::MessageRole::User => "user",
                thulpoff_core::MessageRole::Assistant => "assistant",
                thulpoff_core::MessageRole::Tool => "user", // tool results sent as user
            };
            messages.push(AnthropicMessage {
                role: role_str.to_string(),
                content: msg.content.clone(),
            });
        }

        let tools = request.tools.map(|ts| {
            ts.into_iter()
                .map(|t| AnthropicTool {
                    name: t.name,
                    description: t.description,
                    input_schema: t.parameters,
                })
                .collect()
        });

        let body = AnthropicRequest {
            model: request.model,
            messages,
            max_tokens: request.max_tokens.unwrap_or(4096),
            system,
            temperature: request.temperature,
            tools,
            stop_sequences: request.stop,
        };

        let resp = self
            .client
            .post(ANTHROPIC_API_URL)
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", ANTHROPIC_VERSION)
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await
            .map_err(|e| ThulpoffError::Provider(format!("HTTP error: {}", e)))?;

        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            return Err(ThulpoffError::Provider(format!(
                "Anthropic API {}: {}",
                status, body
            )));
        }

        let api_resp: AnthropicResponse = resp
            .json()
            .await
            .map_err(|e| ThulpoffError::Provider(format!("Parse error: {}", e)))?;

        let mut content = String::new();
        let mut tool_calls = Vec::new();

        for block in api_resp.content {
            match block {
                ContentBlock::Text { text } => content.push_str(&text),
                ContentBlock::ToolUse { id, name, input } => {
                    tool_calls.push(ToolCall {
                        id,
                        name,
                        arguments: input,
                    });
                }
            }
        }

        let finish_reason = match api_resp.stop_reason.as_deref() {
            Some("end_turn") | Some("stop_sequence") => FinishReason::Stop,
            Some("tool_use") => FinishReason::ToolUse,
            Some("max_tokens") => FinishReason::MaxTokens,
            _ => FinishReason::Stop,
        };

        Ok(CompletionResponse {
            content,
            tool_calls,
            usage: TokenUsage {
                input_tokens: api_resp.usage.input_tokens,
                output_tokens: api_resp.usage.output_tokens,
            },
            finish_reason,
        })
    }

    fn name(&self) -> &str {
        "anthropic"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn anthropic_request_serialization() {
        let req = AnthropicRequest {
            model: "claude-sonnet-4-6".into(),
            messages: vec![AnthropicMessage {
                role: "user".into(),
                content: "Hello".into(),
            }],
            max_tokens: 1024,
            system: Some("You are helpful.".into()),
            temperature: Some(0.7),
            tools: None,
            stop_sequences: None,
        };
        let json = serde_json::to_value(&req).unwrap();
        assert_eq!(json["model"], "claude-sonnet-4-6");
        assert_eq!(json["max_tokens"], 1024);
        assert!(json.get("tools").is_none());
    }

    #[test]
    fn anthropic_response_deserialization() {
        let json = r#"{
            "content": [
                {"type": "text", "text": "Hello world"},
                {"type": "tool_use", "id": "tc-1", "name": "read", "input": {"path": "/tmp"}}
            ],
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "stop_reason": "tool_use"
        }"#;
        let resp: AnthropicResponse = serde_json::from_str(json).unwrap();
        assert_eq!(resp.content.len(), 2);
        assert_eq!(resp.usage.input_tokens, 10);
        assert_eq!(resp.stop_reason.as_deref(), Some("tool_use"));
    }

    #[test]
    fn provider_name() {
        let p = AnthropicProvider::new("test-key".into());
        assert_eq!(p.name(), "anthropic");
    }
}
