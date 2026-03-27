use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use thulpoff_core::{
    CompletionRequest, CompletionResponse, FinishReason, LlmProvider, Result, ThulpoffError,
    TokenUsage, ToolCall,
};

const NIM_API_URL: &str = "https://integrate.api.nvidia.com/v1/chat/completions";

pub struct NimProvider {
    client: reqwest::Client,
    api_key: String,
    base_url: String,
}

impl NimProvider {
    pub fn new(api_key: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key,
            base_url: NIM_API_URL.to_string(),
        }
    }

    pub fn with_base_url(api_key: String, base_url: String) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key,
            base_url,
        }
    }

    pub fn from_env() -> Result<Self> {
        let key = std::env::var("NVIDIA_API_KEY")
            .map_err(|_| ThulpoffError::Provider("NVIDIA_API_KEY not set".into()))?;
        Ok(Self::new(key))
    }
}

// OpenAI-compatible chat completions (NIM uses this format)

#[derive(Serialize)]
struct NimRequest {
    model: String,
    messages: Vec<NimMessage>,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_tokens: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    tools: Option<Vec<NimTool>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stop: Option<Vec<String>>,
}

#[derive(Serialize)]
struct NimMessage {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct NimTool {
    #[serde(rename = "type")]
    tool_type: String,
    function: NimFunction,
}

#[derive(Serialize)]
struct NimFunction {
    name: String,
    description: String,
    parameters: serde_json::Value,
}

#[derive(Deserialize)]
struct NimResponse {
    choices: Vec<NimChoice>,
    usage: Option<NimUsage>,
}

#[derive(Deserialize)]
struct NimChoice {
    message: NimResponseMessage,
    finish_reason: Option<String>,
}

#[derive(Deserialize)]
struct NimResponseMessage {
    content: Option<String>,
    tool_calls: Option<Vec<NimToolCall>>,
}

#[derive(Deserialize)]
struct NimToolCall {
    id: String,
    function: NimFunctionCall,
}

#[derive(Deserialize)]
struct NimFunctionCall {
    name: String,
    arguments: String, // NIM returns JSON as string
}

#[derive(Deserialize)]
struct NimUsage {
    prompt_tokens: u32,
    completion_tokens: u32,
}

#[async_trait]
impl LlmProvider for NimProvider {
    async fn complete(&self, request: CompletionRequest) -> Result<CompletionResponse> {
        let messages: Vec<NimMessage> = request
            .messages
            .iter()
            .map(|m| NimMessage {
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
                .map(|t| NimTool {
                    tool_type: "function".into(),
                    function: NimFunction {
                        name: t.name,
                        description: t.description,
                        parameters: t.parameters,
                    },
                })
                .collect()
        });

        let body = NimRequest {
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
                "NIM API {}: {}",
                status, body
            )));
        }

        let api_resp: NimResponse = resp
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

        let usage = api_resp.usage.map(|u| TokenUsage {
            input_tokens: u.prompt_tokens,
            output_tokens: u.completion_tokens,
        }).unwrap_or_default();

        Ok(CompletionResponse {
            content,
            tool_calls,
            usage,
            finish_reason,
        })
    }

    fn name(&self) -> &str {
        "nim"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn nim_request_serialization() {
        let req = NimRequest {
            model: "mistralai/mistral-small-24b-instruct-2501".into(),
            messages: vec![NimMessage {
                role: "user".into(),
                content: "Hello".into(),
            }],
            max_tokens: Some(1024),
            temperature: Some(0.3),
            tools: None,
            stop: None,
        };
        let json = serde_json::to_value(&req).unwrap();
        assert!(json["model"].as_str().unwrap().contains("mistral"));
        assert!(json.get("tools").is_none());
    }

    #[test]
    fn nim_response_deserialization() {
        let json = r#"{
            "choices": [{
                "message": {
                    "content": "Hello world",
                    "tool_calls": null
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10}
        }"#;
        let resp: NimResponse = serde_json::from_str(json).unwrap();
        assert_eq!(resp.choices.len(), 1);
        assert_eq!(resp.choices[0].message.content.as_deref(), Some("Hello world"));
    }

    #[test]
    fn nim_response_with_tool_calls() {
        let json = r#"{
            "choices": [{
                "message": {
                    "content": null,
                    "tool_calls": [{
                        "id": "call-1",
                        "function": {
                            "name": "read_file",
                            "arguments": "{\"path\": \"/tmp/test\"}"
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": {"prompt_tokens": 15, "completion_tokens": 25}
        }"#;
        let resp: NimResponse = serde_json::from_str(json).unwrap();
        let tc = resp.choices[0].message.tool_calls.as_ref().unwrap();
        assert_eq!(tc[0].function.name, "read_file");
    }

    #[test]
    fn provider_name() {
        let p = NimProvider::new("test-key".into());
        assert_eq!(p.name(), "nim");
    }

    #[test]
    fn custom_base_url() {
        let p = NimProvider::with_base_url("key".into(), "http://localhost:8000/v1/chat/completions".into());
        assert_eq!(p.base_url, "http://localhost:8000/v1/chat/completions");
    }
}
