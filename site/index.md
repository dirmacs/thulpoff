---
layout: default.liquid
title: Thulpoff — Skill Distillation for AI Agents
---

<div class="hero">
    <img src="img/thulpoff-logo.svg" alt="thulpoff">
    <h1>Thulpoff</h1>
    <p>Generate, evaluate, and refine SKILL.md files using teacher-student model distillation. Built in Rust.</p>
    <div class="install"><code>cargo install thulpoff-cli</code></div>
</div>

<div class="grid">
    <div class="card">
        <h3>Generate</h3>
        <p>A capable teacher model solves a task. Thulpoff extracts the solution patterns into a reusable SKILL.md file with test cases.</p>
    </div>
    <div class="card">
        <h3>Evaluate</h3>
        <p>Run test cases against student models with and without the skill context. Baseline comparison shows exactly how much the skill helps.</p>
    </div>
    <div class="card">
        <h3>Refine</h3>
        <p>Failed tests feed back to the teacher model, which improves the skill definition. The loop continues until the student passes.</p>
    </div>
</div>

<div class="section">
    <h2>Workspace</h2>
    <table>
        <tr><th>Crate</th><th>What</th></tr>
        <tr><td><code>thulpoff-core</code></td><td>Types, traits, LlmProvider</td></tr>
        <tr><td><code>thulpoff-provider</code></td><td>AnthropicProvider, NimProvider</td></tr>
        <tr><td><code>thulpoff-engine</code></td><td>Generation, Evaluation, Refinement + baseline + history</td></tr>
        <tr><td><code>thulpoff-cli</code></td><td>generate, eval, refine, list, runs</td></tr>
    </table>
</div>

<div class="section">
    <h2>Quick Start</h2>
    <pre><code>thulpoff generate "Write an optimized sorting algorithm" \
  --model claude-opus-4-6 --provider anthropic

thulpoff eval ./skills/sorting/SKILL.md \
  --model mistralai/mistral-small-24b-instruct-2501 --provider nim

thulpoff runs sorting

thulpoff refine ./skills/sorting/SKILL.md \
  --model claude-opus-4-6 --provider anthropic</code></pre>
</div>

<div class="section">
    <h2>Ecosystem</h2>
    <table>
        <tr><th>Project</th><th>What</th></tr>
        <tr><td><a href="https://dirmacs.github.io/thulp">thulp</a></td><td>Execution context engineering</td></tr>
        <tr><td><a href="https://github.com/dirmacs/ares">ares</a></td><td>Agentic retrieval-enhanced server</td></tr>
        <tr><td><a href="https://github.com/dirmacs/pawan">pawan</a></td><td>CLI coding agent</td></tr>
        <tr><td><a href="https://eruka.dirmacs.com">eruka</a></td><td>Context intelligence engine</td></tr>
    </table>
</div>
