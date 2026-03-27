# skills testing

## overview

This repo drives a simple evaluation loop for the model card stats YAML path in the
`hugging-face-evaluation-manager` skill.

The evaluation prompt triggers the skill and writes a YAML file with benchmark scores,
then assertions are checked in `test_eval_assertions.py`.

To generate a CSV summary from run artifacts, use:

```bash
python dev/summarize_runs.py
```

![](./runs-skill-v1/pass_rate_by_model.png)

## what changed vs the original runner

- Each run now executes inside its own **workspace** under `runs/<batch>/run_<n>/workspace`.
- Each run gets a **fresh skills copy** under `runs/<batch>/run_<n>/skills` to prevent agents
  from discovering prior outputs.
- Session history is enabled and persisted per run in
  `runs/<batch>/run_<n>/.fast-agent/sessions/<session_id>/history_*.json`.
- `dev/regrade_runs.py` now prefers session history for timing + turn analysis, with
  fallback to legacy `conversation.json` if present.

## notes and known limitations

- The skills repo is copied per run (no global reset needed).
- We keep the working directory clean by scoping artifacts to the per-run workspace.
- The HF MCP Server is included in context with the `skills` bouquet, so model/dataset
  search, repo details, jobs and docs are available.
- `AGENTS.md` is copied into each workspace to indicate `uv` usage and dependencies.
- For the first run (and probably for the next few) the markdown streaming renderer
  may have a small impact on timings — that’s part of the observation baseline.
- **WARNING:** Make sure you commit changes to the skills repo _before_ running a test,
  since each run snapshots the current state.
