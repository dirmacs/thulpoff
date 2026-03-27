# thulpoff Roadmap

This document outlines the implementation phases for thulpoff.

## Prerequisites ✅ COMPLETE

All prerequisites from thulp have been completed:

| Task | Status | Blocks |
|------|--------|--------|
| Create thulp-skill-files crate | ✅ Done (v0.3.0) | - |
| Implement SkillFile parser | ✅ Done | - |
| Implement SkillWriter | ✅ Done | - |

See [DEPENDENCIES.md](./DEPENDENCIES.md) for details.

---

## Phase 0: thulp Prerequisites ✅ COMPLETE

**Timeline**: Completed in thulp v0.3.0  
**Status**: ✅ All prerequisites satisfied

### Tasks ✅ ALL COMPLETE

1. **Create thulp-skill-files crate** ✅
   - Added to thulp Cargo workspace
   - Basic crate structure complete
   - Added to CI

2. **Implement core types** ✅
   - `SkillFile` struct
   - `SkillFrontmatter` struct
   - Error types

3. **Implement SKILL.md parser** ✅
   - YAML frontmatter extraction
   - Content parsing
   - Variable detection ($ARGUMENTS, etc.)

4. **Implement SkillWriter** ✅
   - Generate SKILL.md from SkillFile
   - Proper frontmatter formatting
   - Content preservation

5. **Testing** ✅
   - Unit tests for parsing
   - Round-trip tests (parse -> write -> parse)
   - Compatibility tests with Claude Code format

### Deliverable ✅

`thulp-skill-files` is part of thulp v0.3.0 (available via workspace dependency)

---

## Phase 1: Core Foundation ← CURRENT PHASE

**Timeline**: 1-2 weeks  
**Priority**: High  
**Dependencies**: ✅ thulp-skill-files (available)

### Tasks

1. **Project scaffolding**
   - Cargo.toml with all dependencies
   - Directory structure
   - CI/CD setup (GitHub Actions)
   - README.md and documentation

2. **Error types**
   - `ThulpoffError` enum with thiserror
   - Result type alias
   - Error conversion traits

3. **LlmProvider trait**
   - Core abstraction
   - Request/Response types
   - Token usage tracking

4. **Anthropic provider**
   - Messages API client
   - Tool calling support
   - Rate limiting
   - **Note**: Can also reuse ares AnthropicClient (v0.4.0+)

5. **OpenAI provider**
   - Chat Completions API client
   - Tool calling support
   - Rate limiting
   - **Note**: Can reuse ares OpenAIClient

6. **Skill file handling**
   - Wrap thulp-skill-files
   - SkillMeta struct
   - Directory management

### Deliverable

Can connect to Claude/OpenAI and write skill files to disk.

### Linear Issues

- [ ] DIR-XX: thulpoff project scaffolding
- [ ] DIR-XX: Implement ThulpoffError types
- [ ] DIR-XX: Implement LlmProvider trait
- [ ] DIR-XX: Implement AnthropicProvider
- [ ] DIR-XX: Implement OpenAIProvider
- [ ] DIR-XX: Skill file handling (wrap thulp-skill-files)

---

## Phase 2: Generation Engine

**Timeline**: 1-2 weeks  
**Priority**: High  
**Dependencies**: Phase 1

### Tasks

1. **Teacher session capture**
   - Multi-turn conversation management
   - Tool call handling
   - Session persistence

2. **Skill extraction**
   - Analyze teacher conversation
   - Extract reusable patterns
   - Generate skill content

3. **Test case generation**
   - LLM-driven test case creation
   - Validation script generation
   - Difficulty classification

4. **Reference extraction**
   - Identify code snippets
   - Extract templates
   - Save to references/ directory

5. **CLI `generate` command**
   - Argument parsing
   - Progress output
   - Error handling

### Deliverable

`thulpoff generate --task "..."` works end-to-end.

### Linear Issues

- [ ] DIR-XX: Implement teacher session capture
- [ ] DIR-XX: Implement skill extraction engine
- [ ] DIR-XX: Implement test case generation
- [ ] DIR-XX: Implement reference extraction
- [ ] DIR-XX: Implement CLI generate command

---

## Phase 3: Evaluation Harness

**Timeline**: 1-2 weeks  
**Priority**: High  
**Dependencies**: Phase 2

### Tasks

1. **Evaluation executor**
   - Run test cases with skill context
   - Run baseline (without skill)
   - Timeout handling

2. **Sandboxed execution**
   - Safe code execution
   - Resource limits
   - Output capture

3. **Scoring system**
   - LLM-based success scoring
   - Rule-based validation
   - Partial credit

4. **Metrics computation**
   - Pass rate calculation
   - Improvement metrics
   - Token usage comparison

5. **Run persistence**
   - Save runs to JSON
   - Run history
   - Run retrieval

6. **CLI `eval` command**
   - Argument parsing
   - Progress bars
   - Results display

### Deliverable

`thulpoff eval --skill X --model Y --baseline` works with comparison metrics.

### Linear Issues

- [ ] DIR-XX: Implement evaluation executor
- [ ] DIR-XX: Implement sandboxed execution
- [ ] DIR-XX: Implement scoring system
- [ ] DIR-XX: Implement metrics computation
- [ ] DIR-XX: Implement run persistence
- [ ] DIR-XX: Implement CLI eval command

---

## Phase 4: Refinement & Polish

**Timeline**: 1-2 weeks  
**Priority**: Medium  
**Dependencies**: Phase 3

### Tasks

1. **Refinement engine**
   - Analyze evaluation failures
   - LLM-driven skill improvement
   - Iterative refinement loop

2. **OpenAI-compatible provider**
   - Generic implementation
   - Tested with Ollama
   - Tested with llama.cpp
   - Tested with NVIDIA NIM

3. **CLI `list` command**
   - List skills
   - Show evaluation results
   - JSON/table output

4. **CLI `runs` command**
   - List run history
   - Filter by skill/model
   - Show run details

5. **Progress indicators**
   - Spinners for long operations
   - Progress bars for batch operations
   - Clear status messages

6. **Documentation**
   - API documentation (rustdoc)
   - Usage examples
   - Troubleshooting guide

### Deliverable

Full CLI parity with HuggingFace upskill.

### Linear Issues

- [ ] DIR-XX: Implement refinement engine
- [ ] DIR-XX: Implement OpenAI-compatible provider
- [ ] DIR-XX: Test with Ollama
- [ ] DIR-XX: Test with NVIDIA NIM
- [ ] DIR-XX: Implement CLI list command
- [ ] DIR-XX: Implement CLI runs command
- [ ] DIR-XX: Add progress indicators
- [ ] DIR-XX: Complete documentation

---

## Phase 5: thulp Integration

**Timeline**: 1-2 weeks  
**Priority**: Medium  
**Dependencies**: Phase 4

### Tasks

1. **thulp-skill-files deep integration**
   - Use SkillPreprocessor
   - Variable interpolation
   - Scope resolution

2. **thulp-registry integration**
   - Register generated skills
   - Skill discovery
   - Marketplace preparation

3. **thulp-workspace integration**
   - Load from workspace directories
   - Project/personal/enterprise scopes
   - Plugin support

4. **lancor integration**
   - Use lancor for llama.cpp
   - Optimized batching
   - Connection pooling

### Deliverable

Full thulp ecosystem integration.

### Linear Issues

- [ ] DIR-XX: Deep thulp-skill-files integration
- [ ] DIR-XX: thulp-registry integration
- [ ] DIR-XX: thulp-workspace integration
- [ ] DIR-XX: lancor integration

---

## Phase 6: Advanced Features (Future)

**Timeline**: Ongoing  
**Priority**: Low  
**Dependencies**: Phase 5

### Potential Features

1. **Parallel evaluation**
   - Concurrent test case execution
   - Rate limit coordination
   - Result aggregation

2. **Skill marketplace**
   - Publish skills
   - Download skills
   - Version management

3. **Web UI**
   - Browser-based interface
   - Visualization
   - Interactive refinement

4. **A/B testing**
   - Compare skill versions
   - Statistical significance
   - Automated selection

5. **Skill composition**
   - Combine multiple skills
   - Skill dependencies
   - Conditional application

6. **Model fine-tuning export**
   - Generate training data from skills
   - Export for model distillation
   - Integration with training pipelines

---

## Timeline Summary

```
Week 0-2:   Phase 0 - thulp prerequisites ✅ COMPLETE
Week 2-4:   Phase 1 - Core foundation ← CURRENT
Week 4-6:   Phase 2 - Generation engine
Week 6-8:   Phase 3 - Evaluation harness
Week 8-10:  Phase 4 - Refinement & polish
Week 10-12: Phase 5 - thulp integration
Week 12+:   Phase 6 - Advanced features (ongoing)
```

## Milestones

| Milestone | Target | Criteria | Status |
|-----------|--------|----------|--------|
| **M0: Prerequisites** | Week 2 | thulp-skill-files published | ✅ DONE |
| **M1: First Skill** | Week 4 | Can generate a skill from task | Pending |
| **M2: First Eval** | Week 6 | Can evaluate skill vs baseline | Pending |
| **M3: MVP** | Week 8 | Full CLI working | Pending |
| **M4: Integration** | Week 10 | thulp ecosystem integrated | Pending |
| **M5: v1.0** | Week 12 | Production ready | Pending |

---

## Risk Factors

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| thulp-skill-files delayed | Blocks all work | Prioritize in thulp roadmap | ✅ Resolved |
| API changes (Anthropic/OpenAI) | Medium | Version-pin, monitor changelogs | Active |
| Local model compatibility | Medium | Test matrix, community feedback | Active |
| Performance at scale | Low | Benchmark early, optimize | Active |

---

## Success Metrics

1. **Generation Quality**
   - Skills improve student model performance by 30%+ on average
   - Generated test cases have >80% validity rate

2. **Evaluation Accuracy**
   - Scorer agrees with human judgment 90%+ of the time
   - Baseline comparison is statistically significant

3. **Usability**
   - CLI commands complete in <60s for typical tasks
   - Error messages are actionable
   - Documentation covers common use cases

4. **Ecosystem Integration**
   - Skills work with Claude Code out of the box
   - Skills work with thulp agents
   - Skills can be shared in marketplace
