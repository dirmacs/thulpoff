# Evaluation Skill Test Suite

This directory contains a one-shot evaluation task and automated assertions for testing the hugging-face-evaluation-manager skill.

## Files

- **ONE_SHOT_EVAL_PROMPT.md** - The prompt to give to the AI agent
- **test_eval_assertions.py** - Automated test script to validate the output
- **olmo_7b_evaluations.yaml** - Expected output file (created by agent)

## Usage

### Step 1: Run the one-shot prompt
Give the agent this instruction:

```
Please read and follow the instructions in ONE_SHOT_EVAL_PROMPT.md
```

### Step 2: Run assertions
After the agent completes the task:

```bash
python test_eval_assertions.py
```

## Expected Results

The test suite validates:

1. ✓ File exists (`olmo_7b_evaluations.yaml`)
2. ✓ Valid model-index YAML structure
3. ✓ Correct model name (OLMo-7B)
4. ✓ Has results section
5. ✓ Correct task type (text-generation)
6. ✓ Has metrics (at least 9 benchmarks)
7. ✓ Expected benchmark types present:
   - arc_challenge, arc_easy, boolq, copa, hellaswag
   - openbookqa, piqa, sciq, winogrande, mmlu, truthfulqa
8. ✓ No hyperparameters or architecture specs
9. ✓ No random baseline scores
10. ✓ All metrics have valid numeric values
11. ✓ Has correct source attribution

## What Makes a Good Assertion?

The test suite checks for:

### Structure Validation
- Proper YAML format
- Required keys present (model-index, results, metrics, source)
- Correct nesting and hierarchy

### Data Quality
- **Unique benchmark types**: Should have 9-11 distinct benchmark types
- **Value ranges**: All scores between 0-100 (percentage scale)
- **Type consistency**: Each metric has name, type, and value

### Filtering Correctness
- **Inclusion**: Only evaluation benchmarks (not training configs)
- **Exclusion**: No hyperparameters (d_model, lr, batch_size, etc.)
- **Exclusion**: No random baselines (only actual model scores)

### Metadata Integrity
- Correct model name matches repo
- Source URL points to correct model
- Task type is appropriate for model

## Key Metrics for allenai/OLMo-7B

Based on the README analysis, expect approximately:
- **11 unique benchmark types** (arc_challenge, arc_easy, boolq, copa, hellaswag, openbookqa, piqa, sciq, winogrande, mmlu, truthfulqa)
- **11 total metrics** (one score per benchmark, from the Llama 7B comparison row)
- **Score range**: 31.5 (MMLU) to 89.5 (SciQ)
- **No duplicates**: Each benchmark appears once
- **No aggregates**: Individual scores only (no averages unless explicitly requested)

## Debugging Failed Assertions

If assertions fail:

1. **Check the extraction**: Run with `--dry-run` to preview
   ```bash
   cd ../skills/hf_model_evaluation
   python scripts/evaluation_manager.py extract-readme --repo-id "allenai/OLMo-7B" --dry-run
   ```

2. **Inspect the output file**:
   ```bash
   cat olmo_7b_evaluations.yaml
   ```

3. **Validate YAML syntax**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('olmo_7b_evaluations.yaml'))"
   ```

4. **Check metric types**:
   ```bash
   python -c "import yaml; data=yaml.safe_load(open('olmo_7b_evaluations.yaml')); print([m['type'] for m in data['model-index'][0]['results'][0]['metrics']])"
   ```
