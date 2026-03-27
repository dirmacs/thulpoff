//! Skill refinement based on evaluation failures.
//!
//! Takes failed test results + the original skill and asks the teacher
//! model to improve the skill definition.

use std::sync::Arc;
use thulpoff_core::{
    CompletionRequest, EvaluationResult, GeneratedSkill, LlmProvider, Message, MessageRole,
    Result,
};

/// Refines skills based on evaluation failures.
pub struct RefinementEngine {
    provider: Arc<dyn LlmProvider>,
}

impl RefinementEngine {
    pub fn new(provider: Arc<dyn LlmProvider>) -> Self {
        Self { provider }
    }

    /// Refine a skill based on evaluation results.
    ///
    /// If the evaluation shows failures, the teacher model is asked to
    /// improve the skill definition to address them.
    pub async fn refine(
        &self,
        skill: &GeneratedSkill,
        eval_result: &EvaluationResult,
        model: &str,
    ) -> Result<GeneratedSkill> {
        if eval_result.overall_score >= 1.0 {
            return Ok(skill.clone());
        }

        let failures: Vec<_> = eval_result
            .test_results
            .iter()
            .filter(|r| !r.passed)
            .collect();

        let failure_summary: Vec<String> = failures
            .iter()
            .map(|f| {
                format!(
                    "Test '{}' (score: {:.2}): output='{}' error='{}'",
                    f.test_name,
                    f.score,
                    truncate(&f.output, 200),
                    f.error.as_deref().unwrap_or("none"),
                )
            })
            .collect();

        let prompt = format!(
            "A skill definition needs improvement. The student model scored {:.0}%.\n\n\
             Current skill:\nName: {}\nDescription: {}\nContent:\n{}\n\n\
             Failed tests ({}/{}):\n{}\n\n\
             Improve the skill definition to address these failures.\n\
             Return the improved skill in the same format:\n\
             DESCRIPTION: <improved description>\n\
             CONTENT:\n<improved markdown steps>",
            eval_result.overall_score * 100.0,
            skill.name,
            skill.description,
            skill.content,
            failures.len(),
            eval_result.test_results.len(),
            failure_summary.join("\n"),
        );

        let request = CompletionRequest {
            messages: vec![
                Message {
                    role: MessageRole::System,
                    content: REFINEMENT_SYSTEM_PROMPT.to_string(),
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
            model: model.to_string(),
            max_tokens: Some(4096),
            temperature: Some(0.4),
            tools: None,
            stop: None,
        };

        let response = self.provider.complete(request).await?;
        self.apply_refinements(skill, &response.content)
    }

    fn apply_refinements(
        &self,
        original: &GeneratedSkill,
        response: &str,
    ) -> Result<GeneratedSkill> {
        let description = extract_field(response, "DESCRIPTION:")
            .unwrap_or_else(|| original.description.clone());

        let content = extract_section(response, "CONTENT:")
            .unwrap_or_else(|| original.content.clone());

        Ok(GeneratedSkill {
            name: original.name.clone(),
            description,
            frontmatter: original.frontmatter.clone(),
            content,
            test_cases: original.test_cases.clone(),
            source_session: original.source_session.clone(),
        })
    }
}

const REFINEMENT_SYSTEM_PROMPT: &str = "\
You are a skill refinement engine. Given a skill definition and its \
test failures, you improve the skill instructions to address the \
failures while preserving what already works. Focus on clarity, \
specificity, and correct tool usage.";

fn extract_field(content: &str, prefix: &str) -> Option<String> {
    content
        .lines()
        .find(|l| l.starts_with(prefix))
        .map(|l| l[prefix.len()..].trim().to_string())
}

fn extract_section(content: &str, after_marker: &str) -> Option<String> {
    let idx = content.find(after_marker)?;
    let rest = &content[idx + after_marker.len()..];
    let section = rest.trim();
    if section.is_empty() { None } else { Some(section.to_string()) }
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}...", &s[..max])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use thulpoff_core::{CompletionResponse, FinishReason, TestCase, TestResult, TokenUsage};

    struct MockTeacher;

    #[async_trait::async_trait]
    impl LlmProvider for MockTeacher {
        async fn complete(&self, _req: CompletionRequest) -> thulpoff_core::Result<CompletionResponse> {
            Ok(CompletionResponse {
                content: "DESCRIPTION: Improved skill\nCONTENT:\n# Better Steps\n1. Do X carefully\n2. Validate output".into(),
                tool_calls: vec![],
                usage: TokenUsage::default(),
                finish_reason: FinishReason::Stop,
            })
        }
        fn name(&self) -> &str { "mock-teacher" }
    }

    fn make_skill() -> GeneratedSkill {
        GeneratedSkill {
            name: "test-skill".into(),
            description: "Original".into(),
            frontmatter: serde_json::json!({}),
            content: "# Steps\n1. Do stuff".into(),
            test_cases: vec![TestCase {
                name: "basic".into(),
                input: serde_json::json!({}),
                expected_behavior: "works".into(),
                pass_criteria: vec!["output".into()],
            }],
            source_session: None,
        }
    }

    #[tokio::test]
    async fn refine_skips_perfect_score() {
        let engine = RefinementEngine::new(Arc::new(MockTeacher));
        let skill = make_skill();
        let eval = EvaluationResult {
            skill_name: "test".into(),
            model: "mock".into(),
            test_results: vec![TestResult {
                test_name: "basic".into(),
                passed: true,
                score: 1.0,
                output: "good".into(),
                error: None,
            }],
            overall_score: 1.0,
            timestamp: chrono::Utc::now(),
        };

        let refined = engine.refine(&skill, &eval, "mock").await.unwrap();
        assert_eq!(refined.content, skill.content, "Should not change on perfect score");
    }

    #[tokio::test]
    async fn refine_improves_on_failure() {
        let engine = RefinementEngine::new(Arc::new(MockTeacher));
        let skill = make_skill();
        let eval = EvaluationResult {
            skill_name: "test".into(),
            model: "mock".into(),
            test_results: vec![TestResult {
                test_name: "basic".into(),
                passed: false,
                score: 0.0,
                output: "wrong".into(),
                error: None,
            }],
            overall_score: 0.0,
            timestamp: chrono::Utc::now(),
        };

        let refined = engine.refine(&skill, &eval, "mock").await.unwrap();
        assert_eq!(refined.description, "Improved skill");
        assert!(refined.content.contains("Better Steps"));
        assert_eq!(refined.name, skill.name, "Name should be preserved");
    }

    #[test]
    fn truncate_short_string() {
        assert_eq!(truncate("hello", 10), "hello");
    }

    #[test]
    fn truncate_long_string() {
        let long = "a".repeat(300);
        let t = truncate(&long, 200);
        assert_eq!(t.len(), 203); // 200 + "..."
        assert!(t.ends_with("..."));
    }
}
