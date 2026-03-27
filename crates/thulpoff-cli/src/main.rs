use std::path::{Path, PathBuf};
use std::sync::Arc;

use clap::{Parser, Subcommand, ValueEnum};
use thulpoff_core::{GeneratedSkill, TeacherSession, TestCase, TokenUsage, LlmProvider};
use thulpoff_engine::{GenerationEngine, EvaluationEngine, RefinementEngine};
use thulpoff_provider::{AnthropicProvider, NimProvider};

#[derive(Parser)]
#[command(name = "thulpoff")]
#[command(about = "Skill distillation for AI agents — generate, evaluate, refine SKILL.md files")]
#[command(version)]
struct Cli {
    /// LLM provider to use
    #[arg(long, value_enum, default_value = "nim", global = true)]
    provider: Provider,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Clone, Copy, ValueEnum)]
enum Provider {
    Anthropic,
    Nim,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate a SKILL.md from a teacher session
    Generate {
        /// Task description for the teacher model
        task: String,
        /// Teacher model to use
        #[arg(long, default_value = "claude-opus-4-6")]
        model: String,
        /// Output directory for the generated skill
        #[arg(long, short, default_value = ".")]
        output: PathBuf,
    },
    /// Evaluate a skill against test cases
    Eval {
        /// Path to the SKILL.md file
        skill: PathBuf,
        /// Student model to evaluate
        #[arg(long, default_value = "mistralai/mistral-small-24b-instruct-2501")]
        model: String,
    },
    /// Refine a skill based on evaluation results
    Refine {
        /// Path to the SKILL.md file
        skill: PathBuf,
        /// Teacher model for refinement
        #[arg(long, default_value = "claude-opus-4-6")]
        model: String,
    },
    /// List available skills in a directory
    List {
        /// Directory to scan for SKILL.md files
        #[arg(long, default_value = "./skills")]
        dir: PathBuf,
    },
}

fn create_provider(provider: Provider) -> Result<Arc<dyn LlmProvider>, String> {
    match provider {
        Provider::Anthropic => {
            AnthropicProvider::from_env()
                .map(|p| Arc::new(p) as Arc<dyn LlmProvider>)
                .map_err(|e| format!("Failed to create Anthropic provider: {}", e))
        }
        Provider::Nim => {
            NimProvider::from_env()
                .map(|p| Arc::new(p) as Arc<dyn LlmProvider>)
                .map_err(|e| format!("Failed to create NIM provider: {}", e))
        }
    }
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    let result = match cli.command {
        Commands::Generate { task, model, output } => {
            cmd_generate(cli.provider, &task, &model, &output).await
        }
        Commands::Eval { skill, model } => {
            cmd_eval(cli.provider, &skill, &model).await
        }
        Commands::Refine { skill, model } => {
            cmd_refine(cli.provider, &skill, &model).await
        }
        Commands::List { dir } => {
            cmd_list(&dir)
        }
    };

    if let Err(e) = result {
        eprintln!("Error: {}", e);
        std::process::exit(1);
    }
}

async fn cmd_generate(
    provider: Provider,
    task: &str,
    model: &str,
    output_dir: &Path,
) -> Result<(), String> {
    let llm = create_provider(provider)?;
    let engine = GenerationEngine::new(llm);

    let session = TeacherSession {
        task_description: task.to_string(),
        messages: vec![],
        tool_calls: vec![],
        model: model.to_string(),
        usage: TokenUsage::default(),
    };

    println!("Generating skill for: {}", task);
    println!("Teacher model: {}", model);

    let skill = engine.generate(&session).await
        .map_err(|e| format!("Generation failed: {}", e))?;

    // Write SKILL.md
    let skill_dir = output_dir.join(&skill.name);
    std::fs::create_dir_all(&skill_dir)
        .map_err(|e| format!("Failed to create directory: {}", e))?;

    let skill_path = skill_dir.join("SKILL.md");
    let content = format_skill_md(&skill);
    std::fs::write(&skill_path, &content)
        .map_err(|e| format!("Failed to write SKILL.md: {}", e))?;

    println!("Generated: {}", skill_path.display());
    println!("  Name: {}", skill.name);
    println!("  Description: {}", skill.description);
    println!("  Test cases: {}", skill.test_cases.len());

    Ok(())
}

async fn cmd_eval(
    provider: Provider,
    skill_path: &Path,
    model: &str,
) -> Result<(), String> {
    let llm = create_provider(provider)?;
    let engine = EvaluationEngine::new(llm);

    let skill = load_skill(skill_path)?;

    println!("Evaluating: {} ({} test cases)", skill.name, skill.test_cases.len());
    println!("Student model: {}", model);

    if skill.test_cases.is_empty() {
        println!("No test cases found — skipping evaluation.");
        return Ok(());
    }

    let result = engine.evaluate(&skill, model).await
        .map_err(|e| format!("Evaluation failed: {}", e))?;

    println!("\nResults:");
    println!("{:<30} {:>6} {:>8}", "TEST", "PASS", "SCORE");
    println!("{}", "-".repeat(46));
    for tr in &result.test_results {
        println!("{:<30} {:>6} {:>7.0}%",
            tr.test_name,
            if tr.passed { "YES" } else { "NO" },
            tr.score * 100.0,
        );
    }
    println!("{}", "-".repeat(46));
    println!("Overall: {:.0}%", result.overall_score * 100.0);

    Ok(())
}

async fn cmd_refine(
    provider: Provider,
    skill_path: &Path,
    model: &str,
) -> Result<(), String> {
    let llm = create_provider(provider)?;
    let eval_engine = EvaluationEngine::new(llm.clone());
    let refine_engine = RefinementEngine::new(llm);

    let skill = load_skill(skill_path)?;

    println!("Evaluating before refinement...");
    let eval_result = eval_engine.evaluate(&skill, model).await
        .map_err(|e| format!("Evaluation failed: {}", e))?;

    println!("Current score: {:.0}%", eval_result.overall_score * 100.0);

    if eval_result.overall_score >= 1.0 {
        println!("Perfect score — no refinement needed.");
        return Ok(());
    }

    println!("Refining with {}...", model);
    let refined = refine_engine.refine(&skill, &eval_result, model).await
        .map_err(|e| format!("Refinement failed: {}", e))?;

    // Write back
    let content = format_skill_md(&refined);
    std::fs::write(skill_path, &content)
        .map_err(|e| format!("Failed to write: {}", e))?;

    println!("Refined: {}", skill_path.display());
    println!("  Description: {}", refined.description);

    Ok(())
}

fn cmd_list(dir: &Path) -> Result<(), String> {
    if !dir.exists() {
        println!("No skills directory at {}", dir.display());
        return Ok(());
    }

    let entries = std::fs::read_dir(dir)
        .map_err(|e| format!("Failed to read directory: {}", e))?;

    let mut found = false;
    println!("{:<25} {}", "SKILL", "DESCRIPTION");
    println!("{}", "-".repeat(60));

    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            let skill_md = path.join("SKILL.md");
            if skill_md.exists() {
                found = true;
                let name = path.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("?");

                let desc = std::fs::read_to_string(&skill_md)
                    .ok()
                    .and_then(|c| extract_description(&c))
                    .unwrap_or_else(|| "(no description)".into());

                println!("{:<25} {}", name, truncate(&desc, 35));
            }
        }
    }

    if !found {
        println!("(no skills found)");
    }

    Ok(())
}

// === Helpers ===

fn format_skill_md(skill: &GeneratedSkill) -> String {
    let frontmatter = serde_json::to_string_pretty(&skill.frontmatter)
        .unwrap_or_else(|_| "{}".into());

    let tests_json = serde_json::to_string_pretty(&skill.test_cases)
        .unwrap_or_else(|_| "[]".into());

    format!(
        "---\n{}\n---\n\n# {}\n\n{}\n\n{}\n\n## Test Cases\n\n```json\n{}\n```\n",
        frontmatter,
        skill.name,
        skill.description,
        skill.content,
        tests_json,
    )
}

fn load_skill(path: &Path) -> Result<GeneratedSkill, String> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| format!("Failed to read {}: {}", path.display(), e))?;

    let (frontmatter_str, body) = if content.starts_with("---") {
        let rest = &content[3..];
        if let Some(end) = rest.find("---") {
            (rest[..end].trim().to_string(), rest[end + 3..].trim().to_string())
        } else {
            (String::new(), content.clone())
        }
    } else {
        (String::new(), content.clone())
    };

    let frontmatter: serde_json::Value = if !frontmatter_str.is_empty() {
        serde_json::from_str(&frontmatter_str).unwrap_or(serde_json::json!({}))
    } else {
        serde_json::json!({})
    };

    let name = frontmatter.get("name")
        .and_then(|v| v.as_str())
        .or_else(|| path.file_stem().and_then(|s| s.to_str()))
        .unwrap_or("unknown")
        .to_string();

    let description = extract_description(&content)
        .unwrap_or_default();

    // Extract test cases from ```json block after "## Test Cases"
    let test_cases = extract_test_cases(&body);

    Ok(GeneratedSkill {
        name,
        description,
        frontmatter,
        content: body.clone(),
        test_cases,
        source_session: None,
    })
}

fn extract_description(content: &str) -> Option<String> {
    // Look for first non-heading, non-empty line after frontmatter
    let body = if content.starts_with("---") {
        content.find("---").and_then(|i| {
            content[i + 3..].find("---").map(|j| &content[i + 3 + j + 3..])
        }).unwrap_or(content)
    } else {
        content
    };

    body.lines()
        .map(|l| l.trim())
        .find(|l| !l.is_empty() && !l.starts_with('#'))
        .map(|l| l.to_string())
}

fn extract_test_cases(body: &str) -> Vec<TestCase> {
    let marker = "## Test Cases";
    if let Some(idx) = body.find(marker) {
        let rest = &body[idx..];
        if let Some(start) = rest.find("```json") {
            let json_start = start + 7;
            let rest2 = &rest[json_start..];
            if let Some(end) = rest2.find("```") {
                let json = rest2[..end].trim();
                return serde_json::from_str(json).unwrap_or_default();
            }
        }
    }
    vec![]
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max { s.to_string() } else { format!("{}...", &s[..max]) }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn format_skill_md_roundtrip() {
        let skill = GeneratedSkill {
            name: "test-skill".into(),
            description: "A test".into(),
            frontmatter: serde_json::json!({"name": "test-skill", "version": "1.0"}),
            content: "Do the thing.".into(),
            test_cases: vec![TestCase {
                name: "basic".into(),
                input: serde_json::json!({}),
                expected_behavior: "works".into(),
                pass_criteria: vec!["output".into()],
            }],
            source_session: None,
        };
        let md = format_skill_md(&skill);
        assert!(md.contains("test-skill"));
        assert!(md.contains("Do the thing."));
        assert!(md.contains("Test Cases"));
    }

    #[test]
    fn extract_description_from_markdown() {
        let content = "---\nname: foo\n---\n\n# Foo\n\nThis is the description.\n\n## Steps\n";
        let desc = extract_description(content).unwrap();
        assert_eq!(desc, "This is the description.");
    }

    #[test]
    fn extract_test_cases_from_body() {
        let body = r#"# Skill

Do stuff.

## Test Cases

```json
[{"name":"basic","input":{},"expected_behavior":"works","pass_criteria":["output"]}]
```
"#;
        let cases = extract_test_cases(body);
        assert_eq!(cases.len(), 1);
        assert_eq!(cases[0].name, "basic");
    }

    #[test]
    fn extract_test_cases_missing_block() {
        let body = "# Skill\n\nJust instructions.";
        let cases = extract_test_cases(body);
        assert!(cases.is_empty());
    }

    #[test]
    fn truncate_works() {
        assert_eq!(truncate("hello world", 5), "hello...");
        assert_eq!(truncate("hi", 5), "hi");
    }

    #[test]
    fn load_skill_with_frontmatter() {
        let dir = std::env::temp_dir().join("thulpoff-cli-test");
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("SKILL.md");
        std::fs::write(&path, "---\n{\"name\":\"test\",\"version\":\"1.0\"}\n---\n\n# Test\n\nDescription here.\n\n## Test Cases\n\n```json\n[]\n```\n").unwrap();

        let skill = load_skill(&path).unwrap();
        assert_eq!(skill.name, "test");
        assert!(skill.test_cases.is_empty());

        std::fs::remove_dir_all(&dir).ok();
    }
}
