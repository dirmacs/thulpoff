//! thulpoff-provider — LLM provider implementations.
//!
//! Concrete implementations of `LlmProvider` for skill distillation:
//! - `AnthropicProvider` — Claude models via Anthropic Messages API
//! - `NimProvider` — NVIDIA NIM models (Mistral, Llama, etc.)

pub use thulpoff_core::{CompletionRequest, CompletionResponse, LlmProvider};

mod anthropic;
mod nim;

pub use anthropic::AnthropicProvider;
pub use nim::NimProvider;
