# thulpoff LLM Providers

This document specifies the LLM provider implementations for thulpoff.

## Overview

thulpoff supports three provider types:
1. **Anthropic** - Claude models via Messages API
2. **OpenAI** - GPT/O-series models via Chat Completions API
3. **OpenAI-Compatible** - Any server implementing OpenAI's API (Ollama, llama.cpp, vLLM, NVIDIA NIM, etc.)

All providers implement the `LlmProvider` trait.

---

## Anthropic Provider

### Configuration

```rust
pub struct AnthropicProvider {
    client: reqwest::Client,
    api_key: String,
    base_url: String,  // https://api.anthropic.com
    default_model: String,
}

impl AnthropicProvider {
    pub fn new(api_key: impl Into<String>) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key: api_key.into(),
            base_url: "https://api.anthropic.com".to_string(),
            default_model: "claude-sonnet-4-20250514".to_string(),
        }
    }
    
    pub fn from_env() -> Result<Self> {
        let api_key = std::env::var("ANTHROPIC_API_KEY")
            .map_err(|_| ThulpoffError::Config("ANTHROPIC_API_KEY not set".into()))?;
        Ok(Self::new(api_key))
    }
}
```

### API Mapping

| thulpoff | Anthropic Messages API |
|----------|------------------------|
| `Message::role` | `messages[].role` |
| `Message::content` | `messages[].content` |
| `ToolCall` | `tool_use` content block |
| `ToolDefinition` | `tools[]` |
| `CompletionRequest::max_tokens` | `max_tokens` |
| `CompletionRequest::temperature` | `temperature` |

### Models

| Model ID | Use Case |
|----------|----------|
| `claude-sonnet-4-20250514` | Best teacher model (default) |
| `claude-3-5-sonnet-20241022` | Alternative teacher |
| `claude-3-5-haiku-20241022` | Default student model |
| `claude-3-haiku-20240307` | Fast student model |

### Example Request

```rust
// Internal API call
let request = serde_json::json!({
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4096,
    "messages": [
        {"role": "user", "content": "Write a CUDA kernel..."}
    ],
    "tools": [
        {
            "name": "execute_code",
            "description": "Execute code in a sandbox",
            "input_schema": {
                "type": "object",
                "properties": {
                    "language": {"type": "string"},
                    "code": {"type": "string"}
                },
                "required": ["language", "code"]
            }
        }
    ]
});

let response = self.client
    .post("https://api.anthropic.com/v1/messages")
    .header("x-api-key", &self.api_key)
    .header("anthropic-version", "2023-06-01")
    .header("content-type", "application/json")
    .json(&request)
    .send()
    .await?;
```

---

## OpenAI Provider

### Configuration

```rust
pub struct OpenAIProvider {
    client: reqwest::Client,
    api_key: String,
    base_url: String,  // https://api.openai.com/v1
    default_model: String,
}

impl OpenAIProvider {
    pub fn new(api_key: impl Into<String>) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key: api_key.into(),
            base_url: "https://api.openai.com/v1".to_string(),
            default_model: "gpt-4o".to_string(),
        }
    }
    
    pub fn from_env() -> Result<Self> {
        let api_key = std::env::var("OPENAI_API_KEY")
            .map_err(|_| ThulpoffError::Config("OPENAI_API_KEY not set".into()))?;
        Ok(Self::new(api_key))
    }
}
```

### API Mapping

| thulpoff | OpenAI Chat Completions API |
|----------|----------------------------|
| `Message::role` | `messages[].role` |
| `Message::content` | `messages[].content` |
| `ToolCall` | `tool_calls[]` |
| `ToolDefinition` | `tools[]` with `type: "function"` |
| `CompletionRequest::max_tokens` | `max_tokens` |
| `CompletionRequest::temperature` | `temperature` |

### Models

| Model ID | Use Case |
|----------|----------|
| `gpt-4o` | Best teacher model |
| `gpt-4o-mini` | Fast student model |
| `o3` | Reasoning-focused teacher |
| `o3-mini` | Fast reasoning student |
| `gpt-4-turbo` | Alternative teacher |

### Example Request

```rust
let request = serde_json::json!({
    "model": "gpt-4o",
    "messages": [
        {"role": "user", "content": "Write a CUDA kernel..."}
    ],
    "max_tokens": 4096,
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "execute_code",
                "description": "Execute code in a sandbox",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string"},
                        "code": {"type": "string"}
                    },
                    "required": ["language", "code"]
                }
            }
        }
    ]
});

let response = self.client
    .post("https://api.openai.com/v1/chat/completions")
    .header("Authorization", format!("Bearer {}", self.api_key))
    .header("Content-Type", "application/json")
    .json(&request)
    .send()
    .await?;
```

---

## OpenAI-Compatible Provider

This provider works with any server implementing the OpenAI Chat Completions API.

### Configuration

```rust
pub struct OpenAICompatProvider {
    client: reqwest::Client,
    base_url: String,
    api_key: Option<String>,
    default_model: String,
}

impl OpenAICompatProvider {
    pub fn new(base_url: impl Into<String>) -> Self {
        Self {
            client: reqwest::Client::new(),
            base_url: base_url.into(),
            api_key: None,
            default_model: "default".to_string(),
        }
    }
    
    pub fn with_api_key(mut self, api_key: impl Into<String>) -> Self {
        self.api_key = Some(api_key.into());
        self
    }
    
    pub fn with_default_model(mut self, model: impl Into<String>) -> Self {
        self.default_model = model.into();
        self
    }
}
```

### Supported Servers

#### Ollama

```rust
let provider = OpenAICompatProvider::new("http://localhost:11434/v1")
    .with_default_model("qwen2.5-coder:32b");
```

| Model | Use Case |
|-------|----------|
| `qwen2.5-coder:32b` | Best local coding model |
| `qwen2.5-coder:7b` | Fast local model |
| `llama3.1:70b` | General purpose |
| `codestral:22b` | Code generation |
| `deepseek-coder-v2:16b` | Code generation |

#### llama.cpp Server

```rust
let provider = OpenAICompatProvider::new("http://localhost:8080/v1")
    .with_default_model("qwen2.5-coder-32b");
```

For llama.cpp, you can optionally use the `lancor` crate for a more optimized client:

```rust
// With lancor feature enabled
use lancor::LlamaCppClient;

let client = LlamaCppClient::new("http://localhost:8080");
let provider = LancorProvider::new(client);
```

#### vLLM

```rust
let provider = OpenAICompatProvider::new("http://localhost:8000/v1")
    .with_default_model("Qwen/Qwen2.5-Coder-32B-Instruct");
```

#### NVIDIA NIM (build.nvidia.com)

```rust
let provider = OpenAICompatProvider::new("https://integrate.api.nvidia.com/v1")
    .with_api_key(std::env::var("NVIDIA_API_KEY")?)
    .with_default_model("meta/llama-3.1-405b-instruct");
```

| Model | Use Case |
|-------|----------|
| `meta/llama-3.1-405b-instruct` | Best NIM model |
| `meta/llama-3.1-70b-instruct` | Fast NIM model |
| `mistralai/mixtral-8x22b-instruct-v0.1` | Alternative |
| `nvidia/nemotron-4-340b-instruct` | NVIDIA's model |
| `deepseek-ai/deepseek-coder-33b-instruct` | Code focused |

#### Together AI

```rust
let provider = OpenAICompatProvider::new("https://api.together.xyz/v1")
    .with_api_key(std::env::var("TOGETHER_API_KEY")?)
    .with_default_model("Qwen/Qwen2.5-Coder-32B-Instruct");
```

#### Groq

```rust
let provider = OpenAICompatProvider::new("https://api.groq.com/openai/v1")
    .with_api_key(std::env::var("GROQ_API_KEY")?)
    .with_default_model("llama-3.3-70b-versatile");
```

---

## Provider Factory

```rust
pub fn create_provider(
    provider_type: ProviderType,
    config: &ProviderConfig,
) -> Result<Box<dyn LlmProvider>> {
    match provider_type {
        ProviderType::Anthropic => {
            let api_key = config.api_key.clone()
                .or_else(|| std::env::var("ANTHROPIC_API_KEY").ok())
                .ok_or_else(|| ThulpoffError::Config("Anthropic API key required".into()))?;
            
            let mut provider = AnthropicProvider::new(api_key);
            if let Some(model) = &config.default_model {
                provider = provider.with_default_model(model);
            }
            Ok(Box::new(provider))
        }
        
        ProviderType::OpenAI => {
            let api_key = config.api_key.clone()
                .or_else(|| std::env::var("OPENAI_API_KEY").ok())
                .ok_or_else(|| ThulpoffError::Config("OpenAI API key required".into()))?;
            
            let mut provider = OpenAIProvider::new(api_key);
            if let Some(model) = &config.default_model {
                provider = provider.with_default_model(model);
            }
            Ok(Box::new(provider))
        }
        
        ProviderType::OpenAICompat => {
            let base_url = config.base_url.clone()
                .ok_or_else(|| ThulpoffError::Config("Base URL required for openai-compat".into()))?;
            
            let mut provider = OpenAICompatProvider::new(base_url);
            if let Some(api_key) = &config.api_key {
                provider = provider.with_api_key(api_key);
            }
            if let Some(model) = &config.default_model {
                provider = provider.with_default_model(model);
            }
            Ok(Box::new(provider))
        }
    }
}
```

---

## Rate Limiting & Retries

All providers implement automatic retry with exponential backoff:

```rust
impl<P: LlmProvider> RetryProvider<P> {
    pub async fn complete_with_retry(
        &self,
        request: CompletionRequest,
    ) -> Result<CompletionResponse> {
        let mut attempts = 0;
        let mut delay = Duration::from_millis(500);
        
        loop {
            match self.inner.complete(request.clone()).await {
                Ok(response) => return Ok(response),
                Err(ThulpoffError::RateLimited { retry_after_secs }) => {
                    if attempts >= self.max_retries {
                        return Err(ThulpoffError::RateLimited { retry_after_secs });
                    }
                    tokio::time::sleep(Duration::from_secs(retry_after_secs)).await;
                }
                Err(e) if e.is_retryable() && attempts < self.max_retries => {
                    tokio::time::sleep(delay).await;
                    delay = std::cmp::min(delay * 2, Duration::from_secs(30));
                }
                Err(e) => return Err(e),
            }
            attempts += 1;
        }
    }
}
```

---

## Tool Calling Support

Not all models support tool calling. The provider trait includes a method to check:

```rust
impl LlmProvider for AnthropicProvider {
    fn supports_tools(&self) -> bool {
        true  // All Claude models support tools
    }
}

impl LlmProvider for OpenAIProvider {
    fn supports_tools(&self) -> bool {
        true  // GPT-4o, o3, etc. support tools
    }
}

impl LlmProvider for OpenAICompatProvider {
    fn supports_tools(&self) -> bool {
        // Depends on the model - assume true, handle errors gracefully
        true
    }
}
```

When a model doesn't support tools, the evaluation harness falls back to prompt-based task execution.

---

## Token Counting

For accurate token counting, providers use:
- **Anthropic**: Response includes `usage.input_tokens` and `usage.output_tokens`
- **OpenAI**: Response includes `usage.prompt_tokens` and `usage.completion_tokens`
- **OpenAI-Compatible**: Response may include usage, otherwise estimate with tiktoken

```rust
/// Estimate token count for a string (fallback)
pub fn estimate_tokens(text: &str) -> u32 {
    // Rough estimate: ~4 characters per token
    (text.len() / 4) as u32
}
```

---

## Environment Variables

| Variable | Provider | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic | API key for Claude |
| `OPENAI_API_KEY` | OpenAI | API key for GPT models |
| `NVIDIA_API_KEY` | NIM | API key for NVIDIA NIM |
| `TOGETHER_API_KEY` | Together | API key for Together AI |
| `GROQ_API_KEY` | Groq | API key for Groq |
