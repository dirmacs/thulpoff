use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "thulpoff")]
#[command(about = "Skill distillation for AI agents — generate, evaluate, refine SKILL.md files")]
#[command(version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
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
        /// Output path for the generated skill
        #[arg(long, short)]
        output: Option<String>,
    },
    /// Evaluate a skill against test cases
    Eval {
        /// Path to the SKILL.md file
        skill: String,
        /// Student model to evaluate
        #[arg(long, default_value = "mistral-small-3-1-24b-instruct")]
        model: String,
    },
    /// Refine a skill based on evaluation results
    Refine {
        /// Path to the SKILL.md file
        skill: String,
    },
    /// List available skills
    List,
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Generate { task, model, output } => {
            println!("Generating skill for: {}", task);
            println!("Teacher model: {}", model);
            if let Some(out) = output {
                println!("Output: {}", out);
            }
            println!("(engine not yet implemented)");
        }
        Commands::Eval { skill, model } => {
            println!("Evaluating: {}", skill);
            println!("Student model: {}", model);
            println!("(engine not yet implemented)");
        }
        Commands::Refine { skill } => {
            println!("Refining: {}", skill);
            println!("(engine not yet implemented)");
        }
        Commands::List => {
            println!("(skill listing not yet implemented)");
        }
    }
}
