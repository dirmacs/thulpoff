//! thulpoff-provider — LLM provider implementations.
//!
//! Concrete implementations of `LlmProvider` for skill distillation:
//! - `AnthropicProvider` — Claude models via Anthropic Messages API
//! - `NimProvider` — NVIDIA NIM models (Mistral, Llama, etc.)
//! - `OpenAiProvider` — OpenAI, Ollama, llama.cpp, vLLM, any OpenAI-compatible endpoint

pub use thulpoff_core::{CompletionRequest, CompletionResponse, LlmProvider};

mod anthropic;
mod nim;
mod openai;

pub use anthropic::AnthropicProvider;
pub use nim::NimProvider;
pub use openai::OpenAiProvider;
