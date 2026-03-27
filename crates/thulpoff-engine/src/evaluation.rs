//! Skill evaluation against student models.
//!
//! Runs test cases from a GeneratedSkill against a student LLM,
//! scoring pass/fail based on criteria matching.

use std::sync::Arc;
use thulpoff_core::{
    CompletionRequest, EvaluationResult, GeneratedSkill, LlmProvider, Message, MessageRole,
    TestCase, TestResult, ThulpoffError, Result,
};

/// Evaluates skills by running test cases against a student model.
pub struct EvaluationEngine {
    provider: Arc<dyn LlmProvider>,
}

impl EvaluationEngine {
    pub fn new(provider: Arc<dyn LlmProvider>) -> Self {
        Self { provider }
    }

    /// Evaluate a skill by running all its test cases.
    pub async fn evaluate(
        &self,
        skill: &GeneratedSkill,
        student_model: &str,
    ) -> Result<EvaluationResult> {
        let mut test_results = Vec::new();

        for test_case in &skill.test_cases {
            let result = self.run_test(skill, test_case, student_model).await?;
            test_results.push(result);
        }

        let total = test_results.len() as f64;
        let passed = test_results.iter().filter(|r| r.passed).count() as f64;
        let overall_score = if total > 0.0 { passed / total } else { 0.0 };

        Ok(EvaluationResult {
            skill_name: skill.name.clone(),
            model: student_model.to_string(),
            test_results,
            overall_score,
            timestamp: chrono::Utc::now(),
        })
    }

    async fn run_test(
        &self,
        skill: &GeneratedSkill,
        test_case: &TestCase,
        model: &str,
    ) -> Result<TestResult> {
        let prompt = format!(
            "You are executing a skill called '{}'.\n\n\
             Skill instructions:\n{}\n\n\
             Test input:\n{}\n\n\
             Expected behavior: {}\n\n\
             Execute the skill and provide your output.",
            skill.name,
            skill.content,
            serde_json::to_string_pretty(&test_case.input).unwrap_or_default(),
            test_case.expected_behavior,
        );

        let request = CompletionRequest {
            messages: vec![Message {
                role: MessageRole::User,
                content: prompt,
                tool_calls: None,
                tool_call_id: None,
            }],
            model: model.to_string(),
            max_tokens: Some(2048),
            temperature: Some(0.2),
            tools: None,
            stop: None,
        };

        let response = self.provider.complete(request).await;

        match response {
            Ok(resp) => {
                let output = resp.content.clone();
                let (passed, score) = self.check_criteria(&output, &test_case.pass_criteria);

                Ok(TestResult {
                    test_name: test_case.name.clone(),
                    passed,
                    score,
                    output,
                    error: None,
                })
            }
            Err(e) => Ok(TestResult {
                test_name: test_case.name.clone(),
                passed: false,
                score: 0.0,
                output: String::new(),
                error: Some(e.to_string()),
            }),
        }
    }

    /// Check pass criteria against the output.
    ///
    /// Each criterion is a substring that should appear in the output.
    /// Score = fraction of criteria met.
    fn check_criteria(&self, output: &str, criteria: &[String]) -> (bool, f64) {
        if criteria.is_empty() {
            return (!output.is_empty(), if output.is_empty() { 0.0 } else { 1.0 });
        }

        let output_lower = output.to_lowercase();
        let met = criteria
            .iter()
            .filter(|c| output_lower.contains(&c.to_lowercase()))
            .count();

        let score = met as f64 / criteria.len() as f64;
        (met == criteria.len(), score)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use thulpoff_core::{CompletionResponse, FinishReason, TokenUsage};

    struct MockStudent {
        response: String,
    }

    #[async_trait::async_trait]
    impl LlmProvider for MockStudent {
        async fn complete(&self, _req: CompletionRequest) -> thulpoff_core::Result<CompletionResponse> {
            Ok(CompletionResponse {
                content: self.response.clone(),
                tool_calls: vec![],
                usage: TokenUsage::default(),
                finish_reason: FinishReason::Stop,
            })
        }
        fn name(&self) -> &str { "mock-student" }
    }

    #[test]
    fn check_criteria_all_met() {
        let engine = EvaluationEngine::new(Arc::new(MockStudent { response: String::new() }));
        let (passed, score) = engine.check_criteria(
            "The function returns a sorted list of integers",
            &["sorted".into(), "list".into(), "integers".into()],
        );
        assert!(passed);
        assert_eq!(score, 1.0);
    }

    #[test]
    fn check_criteria_partial() {
        let engine = EvaluationEngine::new(Arc::new(MockStudent { response: String::new() }));
        let (passed, score) = engine.check_criteria(
            "Returns a list",
            &["sorted".into(), "list".into()],
        );
        assert!(!passed);
        assert_eq!(score, 0.5);
    }

    #[test]
    fn check_criteria_empty_output() {
        let engine = EvaluationEngine::new(Arc::new(MockStudent { response: String::new() }));
        let (passed, score) = engine.check_criteria("", &["something".into()]);
        assert!(!passed);
        assert_eq!(score, 0.0);
    }

    #[test]
    fn check_criteria_no_criteria() {
        let engine = EvaluationEngine::new(Arc::new(MockStudent { response: String::new() }));
        let (passed, score) = engine.check_criteria("some output", &[]);
        assert!(passed);
        assert_eq!(score, 1.0);
    }

    #[tokio::test]
    async fn evaluate_skill_with_passing_tests() {
        let provider = Arc::new(MockStudent {
            response: "The function returns a sorted list of integers".into(),
        });
        let engine = EvaluationEngine::new(provider);

        let skill = GeneratedSkill {
            name: "sort-list".into(),
            description: "Sorts a list".into(),
            frontmatter: serde_json::json!({}),
            content: "Sort the input list".into(),
            test_cases: vec![TestCase {
                name: "basic-sort".into(),
                input: serde_json::json!({"list": [3, 1, 2]}),
                expected_behavior: "Returns sorted list".into(),
                pass_criteria: vec!["sorted".into(), "list".into()],
            }],
            source_session: None,
        };

        let result = engine.evaluate(&skill, "mock").await.unwrap();
        assert_eq!(result.overall_score, 1.0);
        assert!(result.test_results[0].passed);
    }
}
