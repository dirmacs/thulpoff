//! Skill generation from teacher sessions.
//!
//! Takes a TeacherSession (an LLM trace with tool calls) and produces
//! a GeneratedSkill (SKILL.md frontmatter + content + test cases).

use std::sync::Arc;
use thulpoff_core::{
    CompletionRequest, GeneratedSkill, LlmProvider, Message, MessageRole, TeacherSession,
    TestCase, ThulpoffError, Result,
};

/// Extracts skills from teacher LLM sessions.
pub struct GenerationEngine {
    provider: Arc<dyn LlmProvider>,
}

impl GenerationEngine {
    pub fn new(provider: Arc<dyn LlmProvider>) -> Self {
        Self { provider }
    }

    /// Generate a skill from a teacher session trace.
    ///
    /// The teacher session contains the full conversation + tool calls
    /// from a capable model. This engine extracts the pattern into a
    /// reusable SKILL.md definition.
    pub async fn generate(&self, session: &TeacherSession) -> Result<GeneratedSkill> {
        let prompt = self.build_extraction_prompt(session);

        let request = CompletionRequest {
            messages: vec![
                Message {
                    role: MessageRole::System,
                    content: GENERATION_SYSTEM_PROMPT.to_string(),
                    tool_calls: None,
                    tool_call_id: None,
                },
                Message {
                    role: MessageRole::User,
                    content: prompt,
                    tool_calls: None,
                    tool_call_id: None,
                },
            ],
            model: session.model.clone(),
            max_tokens: Some(4096),
            temperature: Some(0.3),
            tools: None,
            stop: None,
        };

        let response = self.provider.complete(request).await?;
        self.parse_skill_response(&response.content, session)
    }

    fn build_extraction_prompt(&self, session: &TeacherSession) -> String {
        let tool_summary: Vec<String> = session
            .tool_calls
            .iter()
            .map(|tc| format!("- {}({})", tc.name, tc.arguments))
            .collect();

        format!(
            "Analyze this AI agent session and extract a reusable skill definition.\n\n\
             Task: {}\n\n\
             Messages: {} turns\n\
             Tool calls used:\n{}\n\n\
             Token usage: {} input, {} output\n\n\
             Extract:\n\
             1. A short skill name (kebab-case)\n\
             2. A description (1-2 sentences)\n\
             3. YAML frontmatter with: name, description, version, tools (list), parameters (list with types)\n\
             4. Step-by-step instructions in markdown\n\
             5. 2-3 test cases with input, expected behavior, and pass criteria\n\n\
             Respond in this exact format:\n\
             SKILL_NAME: <name>\n\
             DESCRIPTION: <description>\n\
             FRONTMATTER:\n```yaml\n<yaml>\n```\n\
             CONTENT:\n<markdown steps>\n\
             TEST_CASES:\n```json\n<json array>\n```",
            session.task_description,
            session.messages.len(),
            tool_summary.join("\n"),
            session.usage.input_tokens,
            session.usage.output_tokens,
        )
    }

    fn parse_skill_response(
        &self,
        content: &str,
        session: &TeacherSession,
    ) -> Result<GeneratedSkill> {
        let name = extract_field(content, "SKILL_NAME:")
            .unwrap_or_else(|| slugify(&session.task_description));
        let description = extract_field(content, "DESCRIPTION:")
            .unwrap_or_else(|| session.task_description.clone());

        let frontmatter = extract_code_block(content, "FRONTMATTER:")
            .and_then(|yaml| serde_json::from_str::<serde_json::Value>(
                &serde_yaml_to_json(&yaml),
            ).ok())
            .unwrap_or_else(|| serde_json::json!({
                "name": name,
                "description": description,
                "version": "1.0",
            }));

        let skill_content = extract_section(content, "CONTENT:")
            .unwrap_or_else(|| format!("# {}\n\n{}", name, description));

        let test_cases = extract_code_block(content, "TEST_CASES:")
            .and_then(|json| serde_json::from_str::<Vec<TestCase>>(&json).ok())
            .unwrap_or_default();

        Ok(GeneratedSkill {
            name,
            description,
            frontmatter,
            content: skill_content,
            test_cases,
            source_session: Some(session.model.clone()),
        })
    }
}

const GENERATION_SYSTEM_PROMPT: &str = "\
You are a skill extraction engine. Given an AI agent session trace \
(task description, messages, tool calls), you extract a reusable \
SKILL.md definition that another agent could follow to accomplish \
the same type of task. Be precise about tool names and parameters.";

fn extract_field(content: &str, prefix: &str) -> Option<String> {
    content
        .lines()
        .find(|l| l.starts_with(prefix))
        .map(|l| l[prefix.len()..].trim().to_string())
}

fn extract_code_block(content: &str, after_marker: &str) -> Option<String> {
    let idx = content.find(after_marker)?;
    let rest = &content[idx..];
    let start = rest.find("```")? + 3;
    let rest2 = &rest[start..];
    // Skip language tag line
    let start2 = rest2.find('\n')? + 1;
    let rest3 = &rest2[start2..];
    let end = rest3.find("```")?;
    Some(rest3[..end].trim().to_string())
}

fn extract_section(content: &str, after_marker: &str) -> Option<String> {
    let idx = content.find(after_marker)?;
    let rest = &content[idx + after_marker.len()..];
    // Take until next marker or end
    let end = rest.find("TEST_CASES:").unwrap_or(rest.len());
    let section = rest[..end].trim();
    if section.is_empty() { None } else { Some(section.to_string()) }
}

fn slugify(s: &str) -> String {
    s.to_lowercase()
        .chars()
        .map(|c| if c.is_alphanumeric() { c } else { '-' })
        .collect::<String>()
        .split('-')
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

fn serde_yaml_to_json(yaml: &str) -> String {
    // Simple YAML→JSON for frontmatter (key: value lines)
    let mut map = serde_json::Map::new();
    for line in yaml.lines() {
        if let Some((key, val)) = line.split_once(':') {
            let k = key.trim().to_string();
            let v = val.trim().to_string();
            map.insert(k, serde_json::Value::String(v));
        }
    }
    serde_json::to_string(&map).unwrap_or_else(|_| "{}".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    use thulpoff_core::TokenUsage;

    #[test]
    fn slugify_works() {
        assert_eq!(slugify("Search and Summarize"), "search-and-summarize");
        assert_eq!(slugify("Fix  bug  #123"), "fix-bug-123");
    }

    #[test]
    fn extract_field_finds_value() {
        let content = "SKILL_NAME: code-review\nDESCRIPTION: Reviews code";
        assert_eq!(extract_field(content, "SKILL_NAME:"), Some("code-review".into()));
        assert_eq!(extract_field(content, "DESCRIPTION:"), Some("Reviews code".into()));
        assert_eq!(extract_field(content, "MISSING:"), None);
    }

    #[test]
    fn extract_code_block_parses() {
        let content = "FRONTMATTER:\n```yaml\nname: test\nversion: 1.0\n```\nrest";
        let block = extract_code_block(content, "FRONTMATTER:").unwrap();
        assert!(block.contains("name: test"));
    }

    #[test]
    fn parse_skill_response_with_minimal_content() {
        let engine = GenerationEngine::new(Arc::new(MockProvider));
        let session = TeacherSession {
            task_description: "Fix the login bug".into(),
            messages: vec![],
            tool_calls: vec![],
            model: "claude-opus-4-6".into(),
            usage: TokenUsage::default(),
        };

        let content = "SKILL_NAME: fix-login-bug\nDESCRIPTION: Fixes login issues\nCONTENT:\n# Steps\n1. Check auth\nTEST_CASES:\n```json\n[]\n```";
        let skill = engine.parse_skill_response(content, &session).unwrap();
        assert_eq!(skill.name, "fix-login-bug");
        assert_eq!(skill.description, "Fixes login issues");
        assert!(skill.content.contains("Check auth"));
    }

    struct MockProvider;

    #[async_trait::async_trait]
    impl LlmProvider for MockProvider {
        async fn complete(&self, _req: CompletionRequest) -> thulpoff_core::Result<thulpoff_core::CompletionResponse> {
            Ok(thulpoff_core::CompletionResponse {
                content: "SKILL_NAME: mock-skill\nDESCRIPTION: A mock\nCONTENT:\nDo things\nTEST_CASES:\n```json\n[]\n```".into(),
                tool_calls: vec![],
                usage: TokenUsage::default(),
                finish_reason: thulpoff_core::FinishReason::Stop,
            })
        }
        fn name(&self) -> &str { "mock" }
    }

    #[tokio::test]
    async fn generate_produces_skill() {
        let engine = GenerationEngine::new(Arc::new(MockProvider));
        let session = TeacherSession {
            task_description: "Test task".into(),
            messages: vec![],
            tool_calls: vec![],
            model: "mock".into(),
            usage: TokenUsage::default(),
        };
        let skill = engine.generate(&session).await.unwrap();
        assert_eq!(skill.name, "mock-skill");
    }
}
