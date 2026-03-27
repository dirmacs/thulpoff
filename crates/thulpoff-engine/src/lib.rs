//! thulpoff-engine — Generation, evaluation, and refinement.
//!
//! Three engines:
//! - `GenerationEngine`: teacher session → skill extraction → SKILL.md
//! - `EvaluationEngine`: run test cases against student models
//! - `RefinementEngine`: analyze failures → improve skills

mod generation;
mod evaluation;
mod refinement;

pub use generation::GenerationEngine;
pub use evaluation::{EvaluationEngine, BaselineComparison};
pub use evaluation::history;
pub use refinement::RefinementEngine;
