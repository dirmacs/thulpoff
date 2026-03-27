# thulpoff Dependencies & Prerequisites

> **Status Update (February 2026)**: All critical dependencies are now available. The `thulp-skill-files` crate is included in thulp v0.3.0 and published to crates.io. thulpoff development can now proceed.

thulpoff depends on the `thulp-skill-files` crate which is now available as part of thulp v0.3.0. This document outlines the dependencies and their current status.

## Dependency Chain

```
thulpoff
    │
    ├── thulp-skill-files (required) ─── ✅ AVAILABLE (thulp v0.3.0)
    │       │
    │       └── thulp-core (exists)
    │
    ├── thulp-core (optional, for tool definitions) ─── ✅ AVAILABLE
    │
    ├── thulp-workspace (optional, for skill discovery) ─── ✅ AVAILABLE
    │
    └── lancor (optional, for llama.cpp client)
```

---

## Required: thulp-skill-files ✅ AVAILABLE

> **Status**: Available in thulp v0.3.0, published to crates.io

### What It Provides

The `thulp-skill-files` crate (proposed in thulp-enhancement-spec.md) provides:

1. **SKILL.md Parsing** - Parse SKILL.md files with YAML frontmatter
2. **SkillFile Struct** - Structured representation of skill files
3. **SkillFrontmatter** - All frontmatter fields (name, description, allowed_tools, etc.)
4. **SkillPreprocessor** - Variable interpolation ($ARGUMENTS, $SELECTION, etc.)
5. **SkillLoader** - Load skills from directories with scope resolution
6. **SkillWriter** - Write SkillFile back to SKILL.md format

### Key Types (from spec)

```rust
// From thulp-skill-files

/// Parsed SKILL.md file
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillFile {
    pub frontmatter: SkillFrontmatter,
    pub content: String,
    pub source_path: Option<PathBuf>,
}

/// YAML frontmatter
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SkillFrontmatter {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub allowed_tools: Option<Vec<String>>,
    
    #[serde(default)]
    pub disable_model_invocation: bool,
    
    #[serde(default = "default_true")]
    pub user_invocable: bool,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub requires_approval: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context: Option<SkillContext>,
}

/// Loading skills from directories
pub struct SkillLoader {
    config: SkillLoaderConfig,
}

#[derive(Debug, Clone)]
pub struct SkillLoaderConfig {
    pub project_dir: Option<PathBuf>,
    pub personal_dir: Option<PathBuf>,
    pub enterprise_dir: Option<PathBuf>,
    pub plugin_dirs: Vec<PathBuf>,
    pub max_depth: usize,
}
```

### Why thulpoff Needs It

thulpoff needs `thulp-skill-files` for:

1. **Skill Generation** - Write generated skills in the correct SKILL.md format
2. **Skill Loading** - Load existing skills for evaluation
3. **Frontmatter Handling** - Proper YAML frontmatter parsing/generation
4. **Format Compatibility** - Ensure generated skills work with Claude Code and thulp

Without `thulp-skill-files`, thulpoff would need to:
- Duplicate all SKILL.md parsing logic
- Risk format incompatibilities
- Miss future format enhancements

---

## Implementation Order

### Phase 0: thulp Prerequisites ✅ COMPLETE

These changes have been completed in thulp v0.3.0:

| Task | Crate | Description | Status |
|------|-------|-------------|--------|
| Create thulp-skill-files crate | thulp | New crate for SKILL.md parsing | ✅ Done |
| Implement SkillFile parser | thulp-skill-files | Parse SKILL.md with frontmatter | ✅ Done |
| Implement SkillFrontmatter | thulp-skill-files | All frontmatter fields | ✅ Done |
| Implement SkillWriter | thulp-skill-files | Write SkillFile to SKILL.md | ✅ Done |
| Implement SkillLoader | thulp-skill-files | Load from directories | ✅ Done |
| Implement SkillPreprocessor | thulp-skill-files | Variable interpolation | ✅ Done |
| Update thulp-registry | thulp-registry | SkillRegistry for skill management | ✅ Done |
| Update thulp-workspace | thulp-workspace | SkillWorkspace integration | ✅ Done |

### Minimum Viable thulp-skill-files ✅ AVAILABLE

All required features are now available in thulp v0.3.0:

```rust
// Minimum API surface needed by thulpoff

/// Parse a SKILL.md file
pub fn parse_skill_file(content: &str) -> Result<SkillFile>;

/// Parse from file path
pub fn parse_skill_file_from_path(path: &Path) -> Result<SkillFile>;

/// Write a SkillFile to SKILL.md format
pub fn write_skill_file(skill: &SkillFile) -> String;

/// Write to file path
pub fn write_skill_file_to_path(skill: &SkillFile, path: &Path) -> Result<()>;
```

The more advanced features (SkillLoader, SkillPreprocessor, scope resolution) are also available in v0.3.0.

---

## Optional Dependencies

### thulp-core ✅ AVAILABLE

Provides core types like `ToolDefinition` and `ToolCall`. thulpoff can optionally use these for consistency with the thulp ecosystem.

```toml
[dependencies]
thulp-core = { version = "0.1", optional = true }

[features]
thulp = ["dep:thulp-core"]
```

If not using thulp-core, thulpoff defines its own compatible types.

### thulp-workspace ✅ AVAILABLE

For loading skills from standard workspace directories:

```rust
use thulp_workspace::SkillWorkspace;

let workspace = SkillWorkspace::discover(".")?;
let skills = workspace.load_skills()?;
```

### lancor

For optimized llama.cpp client:

```rust
use lancor::LlamaCppClient;

let client = LlamaCppClient::new("http://localhost:8080");
```

---

## Cargo.toml (thulpoff)

```toml
[package]
name = "thulpoff"
version = "0.1.0"
edition = "2021"

[dependencies]
# Required - now available
thulp-skill-files = "0.3"  # Available in thulp v0.3.0

# Core
tokio = { version = "1.0", features = ["full"] }
async-trait = "0.1"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
serde_yaml = "0.9"
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }
thiserror = "2.0"
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1.0", features = ["v4", "serde"] }
clap = { version = "4.0", features = ["derive"] }

# ares integration - can reuse LLM clients
ares = { path = "../ares" }  # Use ares OpenAIClient, AnthropicClient, etc.

# Optional thulp integration
thulp-core = { version = "0.3", optional = true }
thulp-workspace = { version = "0.3", optional = true }
lancor = { version = "0.1", optional = true }

[features]
default = []
thulp = ["dep:thulp-core", "dep:thulp-workspace"]
lancor = ["dep:lancor"]
full = ["thulp", "lancor"]
```

---

## Migration Strategy

> **Note**: This section is now historical context. The recommended approach was followed and thulp-skill-files is now available.

~~If thulp-skill-files takes longer than expected, thulpoff could:~~

1. ~~**Start with internal implementation** - Create a minimal SKILL.md parser internally~~
2. ~~**Design for compatibility** - Match the proposed thulp-skill-files API~~
3. ~~**Migrate later** - Replace internal implementation with thulp-skill-files dependency~~

~~However, this approach has risks:~~
~~- Potential format incompatibilities~~
~~- Duplicate maintenance effort~~
~~- API drift between implementations~~

~~**Recommendation**: Wait for thulp-skill-files to ensure ecosystem consistency.~~

**Actual outcome**: thulp-skill-files was completed in thulp v0.3.0. thulpoff can now proceed with the recommended approach.

---

## Tracking

### Linear Issues ✅ COMPLETED (thulp)

All prerequisite thulp issues have been completed:

1. ✅ **Create thulp-skill-files crate** - Project scaffolding
2. ✅ **Implement SkillFile and SkillFrontmatter** - Core types
3. ✅ **Implement SKILL.md parser** - Parse frontmatter + content
4. ✅ **Implement SkillWriter** - Generate SKILL.md from SkillFile
5. ✅ **Add thulp-skill-files to workspace** - Cargo workspace integration
6. ✅ **Publish thulp-skill-files to crates.io** - Available as thulp v0.3.0

### Blocking Relationship ✅ RESOLVED

```
thulp issues (✅ COMPLETE):
├── Create thulp-skill-files crate      ✅
├── Implement SkillFile parser          ✅
├── Implement SkillWriter               ✅
└── Publish to crates.io                ✅ (thulp v0.3.0)
        │
        ▼ (UNBLOCKED)
thulpoff issues (READY TO START):
├── Phase 1: Core Foundation
├── Phase 2: Generation Engine
└── ...
```

---

## References

- [thulp-enhancement-spec.md](../../ehb/thulp-enhancement-spec.md) - Full specification for thulp-skill-files
- [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills) - SKILL.md format reference
- [thulp repository](https://github.com/dirmacs/thulp) - Current thulp implementation
