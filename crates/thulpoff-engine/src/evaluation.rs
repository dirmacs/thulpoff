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

    /// Evaluate with baseline comparison.
    ///
    /// Runs the student model TWICE: once with the skill context (skilled),
    /// once without (baseline). Returns both results for comparison.
    pub async fn evaluate_with_baseline(
        &self,
        skill: &GeneratedSkill,
        student_model: &str,
    ) -> Result<BaselineComparison> {
        // Run WITH skill context (normal evaluation)
        let skilled = self.evaluate(skill, student_model).await?;

        // Run WITHOUT skill context (baseline — just the test case, no skill instructions)
        let mut baseline_results = Vec::new();
        for test_case in &skill.test_cases {
            let result = self.run_test_baseline(test_case, student_model).await?;
            baseline_results.push(result);
        }

        let total = baseline_results.len() as f64;
        let passed = baseline_results.iter().filter(|r| r.passed).count() as f64;
        let baseline_score = if total > 0.0 { passed / total } else { 0.0 };

        let baseline = EvaluationResult {
            skill_name: format!("{} (baseline)", skill.name),
            model: student_model.to_string(),
            test_results: baseline_results,
            overall_score: baseline_score,
            timestamp: chrono::Utc::now(),
        };

        let improvement = skilled.overall_score - baseline.overall_score;

        Ok(BaselineComparison {
            skilled,
            baseline,
            improvement,
        })
    }

    /// Run a test WITHOUT skill context (baseline).
    async fn run_test_baseline(
        &self,
        test_case: &TestCase,
        model: &str,
    ) -> Result<TestResult> {
        let prompt = format!(
            "Task:\n{}\n\nInput:\n{}\n\nProvide your output.",
            test_case.expected_behavior,
            serde_json::to_string_pretty(&test_case.input).unwrap_or_default(),
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

        match self.provider.complete(request).await {
            Ok(resp) => {
                let (passed, score) = self.check_criteria(&resp.content, &test_case.pass_criteria);
                Ok(TestResult {
                    test_name: test_case.name.clone(),
                    passed,
                    score,
                    output: resp.content,
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
}

/// Result of a baseline comparison evaluation.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BaselineComparison {
    /// Results WITH skill context
    pub skilled: EvaluationResult,
    /// Results WITHOUT skill context (baseline)
    pub baseline: EvaluationResult,
    /// Score improvement (skilled - baseline). Positive = skill helps.
    pub improvement: f64,
}

/// Persist and load evaluation results.
pub mod history {
    use super::*;
    use std::path::{Path, PathBuf};

    /// Save an evaluation result to disk.
    pub fn save_result(
        base_dir: &Path,
        result: &EvaluationResult,
    ) -> std::io::Result<PathBuf> {
        let dir = base_dir
            .join(".thulpoff")
            .join("runs")
            .join(&result.skill_name);
        std::fs::create_dir_all(&dir)?;

        let filename = format!("{}.json", result.timestamp.format("%Y%m%d-%H%M%S"));
        let path = dir.join(&filename);

        let json = serde_json::to_string_pretty(result)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e))?;
        std::fs::write(&path, json)?;

        Ok(path)
    }

    /// Load the most recent evaluation result for a skill.
    pub fn load_last_result(
        base_dir: &Path,
        skill_name: &str,
    ) -> std::io::Result<Option<EvaluationResult>> {
        let dir = base_dir
            .join(".thulpoff")
            .join("runs")
            .join(skill_name);

        if !dir.exists() {
            return Ok(None);
        }

        let mut entries: Vec<_> = std::fs::read_dir(&dir)?
            .filter_map(|e| e.ok())
            .filter(|e| e.path().extension().map_or(false, |ext| ext == "json"))
            .collect();

        entries.sort_by(|a, b| b.file_name().cmp(&a.file_name()));

        if let Some(entry) = entries.first() {
            let content = std::fs::read_to_string(entry.path())?;
            let result: EvaluationResult = serde_json::from_str(&content)
                .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
            Ok(Some(result))
        } else {
            Ok(None)
        }
    }

    /// List all runs for a skill.
    pub fn list_runs(
        base_dir: &Path,
        skill_name: &str,
    ) -> std::io::Result<Vec<RunSummary>> {
        let dir = base_dir
            .join(".thulpoff")
            .join("runs")
            .join(skill_name);

        if !dir.exists() {
            return Ok(vec![]);
        }

        let mut summaries = Vec::new();
        for entry in std::fs::read_dir(&dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.extension().map_or(false, |ext| ext == "json") {
                if let Ok(content) = std::fs::read_to_string(&path) {
                    if let Ok(result) = serde_json::from_str::<EvaluationResult>(&content) {
                        summaries.push(RunSummary {
                            filename: entry.file_name().to_string_lossy().to_string(),
                            skill_name: result.skill_name.clone(),
                            model: result.model.clone(),
                            score: result.overall_score,
                            tests: result.test_results.len(),
                            passed: result.test_results.iter().filter(|r| r.passed).count(),
                            timestamp: result.timestamp.to_rfc3339(),
                        });
                    }
                }
            }
        }

        summaries.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        Ok(summaries)
    }

    /// Summary of a saved run.
    #[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
    pub struct RunSummary {
        pub filename: String,
        pub skill_name: String,
        pub model: String,
        pub score: f64,
        pub tests: usize,
        pub passed: usize,
        pub timestamp: String,
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

    #[tokio::test]
    async fn baseline_comparison_shows_improvement() {
        let provider = Arc::new(MockStudent {
            response: "The function returns a sorted list of integers".into(),
        });
        let engine = EvaluationEngine::new(provider);

        let skill = GeneratedSkill {
            name: "sort-list".into(),
            description: "Sorts a list".into(),
            frontmatter: serde_json::json!({}),
            content: "Sort the input list using an efficient algorithm".into(),
            test_cases: vec![TestCase {
                name: "basic".into(),
                input: serde_json::json!({"list": [3, 1, 2]}),
                expected_behavior: "Returns sorted list".into(),
                pass_criteria: vec!["sorted".into(), "list".into()],
            }],
            source_session: None,
        };

        let comparison = engine.evaluate_with_baseline(&skill, "mock").await.unwrap();
        // Both should pass with mock (same response regardless of context)
        assert_eq!(comparison.skilled.overall_score, comparison.baseline.overall_score);
        assert_eq!(comparison.improvement, 0.0);
    }

    #[test]
    fn save_and_load_result() {
        let dir = std::env::temp_dir().join("thulpoff-history-test");
        let _ = std::fs::remove_dir_all(&dir);

        let result = EvaluationResult {
            skill_name: "test-skill".into(),
            model: "mock".into(),
            test_results: vec![TestResult {
                test_name: "basic".into(),
                passed: true,
                score: 1.0,
                output: "ok".into(),
                error: None,
            }],
            overall_score: 1.0,
            timestamp: chrono::Utc::now(),
        };

        let path = history::save_result(&dir, &result).unwrap();
        assert!(path.exists());

        let loaded = history::load_last_result(&dir, "test-skill").unwrap().unwrap();
        assert_eq!(loaded.skill_name, "test-skill");
        assert_eq!(loaded.overall_score, 1.0);

        let runs = history::list_runs(&dir, "test-skill").unwrap();
        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].passed, 1);

        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn load_last_result_no_history() {
        let dir = std::env::temp_dir().join("thulpoff-no-history");
        let result = history::load_last_result(&dir, "nonexistent").unwrap();
        assert!(result.is_none());
    }

    #[test]
    fn baseline_comparison_serde() {
        let bc = BaselineComparison {
            skilled: EvaluationResult {
                skill_name: "test".into(),
                model: "mock".into(),
                test_results: vec![],
                overall_score: 0.8,
                timestamp: chrono::Utc::now(),
            },
            baseline: EvaluationResult {
                skill_name: "test (baseline)".into(),
                model: "mock".into(),
                test_results: vec![],
                overall_score: 0.5,
                timestamp: chrono::Utc::now(),
            },
            improvement: 0.3,
        };
        let json = serde_json::to_string(&bc).unwrap();
        let parsed: BaselineComparison = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.improvement, 0.3);
    }
}
