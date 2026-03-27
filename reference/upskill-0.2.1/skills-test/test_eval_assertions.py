#!/usr/bin/env python3
"""
Assertions for testing the evaluation extraction output.
Run this after the one-shot prompt completes.
"""

import sys
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class ValidationResult:
    """Structured result from validation with metrics."""
    passed: bool
    assertions_passed: int
    assertions_total: int
    metrics_count: int
    benchmarks_found: list[str] = field(default_factory=list)
    error_message: str | None = None


EXPECTED_METRICS: dict[str, float] = {
    "arc_challenge": 48.5,
    "arc_easy": 65.4,
    "boolq": 73.4,
    "copa": 90.0,
    "hellaswag": 76.4,
    "openbookqa": 50.2,
    "piqa": 78.4,
    "sciq": 93.8,
    "winogrande": 67.9,
    "mmlu": 28.3,
    "truthfulqa": 36.0,
}

ALLOWED_MODEL_NAME_PATTERNS = {"olmo 7b", "olmo-7b"}

# The base assertions cover structure, types, and safety checks.
# We then add one assertion per expected metric value.
BASE_ASSERTIONS = 12
VALUE_ASSERTIONS = len(EXPECTED_METRICS)
ASSERTIONS_TOTAL = BASE_ASSERTIONS + VALUE_ASSERTIONS


def _model_name_matches(name: str) -> bool:
    """Check if model name contains 'olmo 7b' or 'olmo-7b' (case-insensitive)."""
    name_lower = name.lower()
    return any(pattern in name_lower for pattern in ALLOWED_MODEL_NAME_PATTERNS)


def _normalize_metric_type(metric_type: str) -> str:
    metric_type = metric_type.lower().replace(" ", "_")
    metric_type = metric_type.replace("_(mc2)", "").replace("_(5_shot_mc)", "")
    if "truthful" in metric_type:
        return "truthfulqa"
    if "mmlu" in metric_type:
        return "mmlu"
    return metric_type


def _assert_metric_values(metrics: Iterable[dict], expected: dict[str, float]):
    """Return a dict of normalized metric type -> value for validation."""
    metric_map: dict[str, float] = {}
    for m in metrics:
        m_type = _normalize_metric_type(m["type"])
        metric_map[m_type] = m["value"]
    for metric, expected_value in expected.items():
        assert metric in metric_map, f"Missing expected metric: {metric}"
        assert metric_map[metric] == expected_value, (
            f"Metric {metric} has value {metric_map[metric]}, expected {expected_value}"
        )
    return metric_map

def validate_evaluation_file(
    output_file: Path,
    *,
    expected_source: str = "huggingface.co/allenai/OLMo-7B",
    min_expected_benchmarks: int = 9,
    expected_benchmarks: set[str] | None = None,
    expected_metrics: dict[str, float] | None = None,
):
    """Validate an evaluation YAML file and raise on failure."""

    assert output_file.exists(), f"Output file '{output_file}' not found"
    print("✓ File exists")

    # Load YAML
    with open(output_file, 'r') as f:
        data = yaml.safe_load(f)

    # Assertion 2: Has model-index structure
    assert 'model-index' in data, "Missing 'model-index' key"
    assert len(data['model-index']) > 0, "model-index is empty"
    print("✓ Valid model-index structure")

    model_entry = data['model-index'][0]

    # Assertion 3: Model name contains olmo 7b or olmo-7b (case-insensitive)
    model_name = model_entry['name']
    assert _model_name_matches(model_name), f"Model name '{model_name}' does not contain 'olmo 7b' or 'olmo-7b'"
    print("✓ Correct model name")
    
    # Assertion 4: Has results
    assert 'results' in model_entry, "Missing 'results' key"
    assert len(model_entry['results']) > 0, "Results is empty"
    print("✓ Has results")
    
    result = model_entry['results'][0]
    
    # Assertion 5: Task type is text-generation
    assert result['task']['type'] == 'text-generation', f"Task type is {result['task']['type']}"
    print("✓ Correct task type")
    
    # Assertion 6: Has metrics
    assert 'metrics' in result, "Missing 'metrics' key"
    metrics = result['metrics']
    assert len(metrics) > 0, "Metrics list is empty"
    print(f"✓ Has {len(metrics)} metrics")

    # Assertion 6b: Exact metric count
    expected_metrics = expected_metrics or EXPECTED_METRICS
    assert len(metrics) >= len(expected_metrics), (
        f"Metrics list has {len(metrics)} entries, expected at least {len(expected_metrics)}"
    )
    print("✓ Metrics count meets expectation")
    
    # Assertion 7: Expected benchmark types
    expected_benchmarks = expected_benchmarks or set(expected_metrics.keys())
    
    # Extract metric types (normalize to handle variations)
    metric_types = set()
    for m in metrics:
        metric_type = _normalize_metric_type(m['type'])
        metric_types.add(metric_type)
    
    found_benchmarks = expected_benchmarks & metric_types
    assert len(found_benchmarks) >= min_expected_benchmarks, f"Only found {len(found_benchmarks)} expected benchmarks: {found_benchmarks}"
    print(f"✓ Found {len(found_benchmarks)} expected benchmark types: {sorted(found_benchmarks)}")
    
    # Assertion 8: No unwanted metric types (hyperparameters, architecture)
    unwanted_types = {
        'd_model', 'num_heads', 'num_layers', 'batch_size', 'peak_lr', 
        'warmup_steps', 'weight_decay', 'beta1', 'beta2', 'epsilon',
        'sequence_length', '1b', '7b'
    }
    
    unwanted_found = set()
    for m in metrics:
        metric_type = m['type'].lower()
        for unwanted in unwanted_types:
            if unwanted in metric_type:
                unwanted_found.add(metric_type)
    
    assert len(unwanted_found) == 0, f"Found unwanted metric types: {unwanted_found}"
    print("✓ No hyperparameters or architecture specs included")
    
    # Assertion 9: No random baseline scores
    for m in metrics:
        assert 'random' not in m['name'].lower(), f"Found random baseline: {m['name']}"
    print("✓ No random baseline scores")
    
    # Assertion 10: All metrics have valid values
    for m in metrics:
        assert 'value' in m, f"Metric {m['name']} missing value"
        assert isinstance(m['value'], (int, float)), f"Metric {m['name']} value is not numeric"
        assert m['value'] > 0, f"Metric {m['name']} has invalid value: {m['value']}"
    print("✓ All metrics have valid numeric values")

    # Assertion 11b: Exact metric values
    metric_map = _assert_metric_values(metrics, expected_metrics)
    print(f"✓ Metric values match expected scores for {len(metric_map)} metrics")
    
    # Assertion 11: Has source attribution
    assert 'source' in result, "Missing 'source' key"
    assert 'url' in result['source'], "Missing source URL"
    assert expected_source in result['source']['url'], "Incorrect source URL"
    print("✓ Has correct source attribution")
    
    # Summary
    print("\n" + "="*50)
    print(f"ALL ASSERTIONS PASSED ✓")
    print(f"Total metrics: {len(metrics)}")
    print(f"Unique benchmark types: {len(metric_types)}")
    print(f"Expected benchmarks found: {len(found_benchmarks)}/{len(expected_benchmarks)}")
    print("="*50)
    
    return True

def test_olmo_evaluation_output(path: str | Path | None = None):
    """Test the generated evaluation YAML file."""
    output_file = Path(path) if path else Path("olmo_7b_evaluations.yaml")
    return validate_evaluation_file(output_file)


def validate_with_metrics(
    output_file: Path,
    *,
    expected_source: str = "huggingface.co/allenai/OLMo-7B",
    min_expected_benchmarks: int = 9,
    expected_benchmarks: set[str] | None = None,
    expected_metrics: dict[str, float] | None = None,
) -> ValidationResult:
    """Validate an evaluation YAML file and return structured metrics.

    This is a wrapper around validate_evaluation_file that catches exceptions
    and returns a ValidationResult with pass/fail status and assertion counts.
    """
    assertions_passed = 0
    assertions_total = ASSERTIONS_TOTAL
    metrics_count = 0
    benchmarks_found: list[str] = []
    expected_metrics = expected_metrics or EXPECTED_METRICS
    expected_benchmarks = expected_benchmarks or set(expected_metrics.keys())

    try:
        # Check file exists (assertion 1)
        if not output_file.exists():
            return ValidationResult(
                passed=False,
                assertions_passed=0,
                assertions_total=assertions_total,
                metrics_count=0,
                benchmarks_found=[],
                error_message=f"Output file '{output_file}' not found",
            )
        assertions_passed += 1

        # Load YAML
        with open(output_file, 'r') as f:
            data = yaml.safe_load(f)

        # Assertion 2: Has model-index structure
        if 'model-index' not in data or len(data['model-index']) == 0:
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=0,
                benchmarks_found=[],
                error_message="Missing or empty 'model-index' key",
            )
        assertions_passed += 1

        model_entry = data['model-index'][0]

        # Assertion 3: Model name contains olmo 7b or olmo-7b (case-insensitive)
        model_name = model_entry.get('name', '')
        if not _model_name_matches(model_name):
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=0,
                benchmarks_found=[],
                error_message=f"Model name '{model_name}' does not contain 'olmo 7b' or 'olmo-7b'",
            )
        assertions_passed += 1

        # Assertion 4: Has results
        if 'results' not in model_entry or len(model_entry['results']) == 0:
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=0,
                benchmarks_found=[],
                error_message="Missing or empty 'results' key",
            )
        assertions_passed += 1

        result = model_entry['results'][0]

        # Assertion 5: Task type is text-generation
        task_type = result.get('task', {}).get('type')
        if task_type != 'text-generation':
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=0,
                benchmarks_found=[],
                error_message=f"Task type is '{task_type}', expected 'text-generation'",
            )
        assertions_passed += 1

        # Assertion 6: Has metrics
        if 'metrics' not in result or len(result['metrics']) == 0:
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=0,
                benchmarks_found=[],
                error_message="Missing or empty 'metrics' key",
            )
        metrics = result['metrics']
        metrics_count = len(metrics)
        assertions_passed += 1

        # Assertion 6b: Exact metric count
        if len(metrics) < len(expected_metrics):
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=metrics_count,
                benchmarks_found=[],
                error_message=f"Metrics list has {len(metrics)} entries, expected at least {len(expected_metrics)}",
            )
        assertions_passed += 1

        # Assertion 7: Expected benchmark types
        metric_types = set()
        for m in metrics:
            metric_type = _normalize_metric_type(m['type'])
            metric_types.add(metric_type)

        found_benchmarks = expected_benchmarks & metric_types
        benchmarks_found = sorted(found_benchmarks)

        if len(found_benchmarks) < min_expected_benchmarks:
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=metrics_count,
                benchmarks_found=benchmarks_found,
                error_message=f"Only found {len(found_benchmarks)} expected benchmarks: {found_benchmarks}",
            )
        assertions_passed += 1

        # Assertion 8: No unwanted metric types
        unwanted_types = {
            'd_model', 'num_heads', 'num_layers', 'batch_size', 'peak_lr',
            'warmup_steps', 'weight_decay', 'beta1', 'beta2', 'epsilon',
            'sequence_length', '1b', '7b'
        }

        unwanted_found = set()
        for m in metrics:
            metric_type = m['type'].lower()
            for unwanted in unwanted_types:
                if unwanted in metric_type:
                    unwanted_found.add(metric_type)

        if len(unwanted_found) > 0:
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=metrics_count,
                benchmarks_found=benchmarks_found,
                error_message=f"Found unwanted metric types: {unwanted_found}",
            )
        assertions_passed += 1

        # Assertion 9: No random baseline scores
        for m in metrics:
            if 'random' in m.get('name', '').lower():
                return ValidationResult(
                    passed=False,
                    assertions_passed=assertions_passed,
                    assertions_total=assertions_total,
                    metrics_count=metrics_count,
                    benchmarks_found=benchmarks_found,
                    error_message=f"Found random baseline: {m['name']}",
                )
        assertions_passed += 1

        # Assertion 10: All metrics have valid values
        for m in metrics:
            if 'value' not in m:
                return ValidationResult(
                    passed=False,
                    assertions_passed=assertions_passed,
                    assertions_total=assertions_total,
                    metrics_count=metrics_count,
                    benchmarks_found=benchmarks_found,
                    error_message=f"Metric {m.get('name')} missing value",
                )
            if not isinstance(m['value'], (int, float)):
                return ValidationResult(
                    passed=False,
                    assertions_passed=assertions_passed,
                    assertions_total=assertions_total,
                    metrics_count=metrics_count,
                    benchmarks_found=benchmarks_found,
                    error_message=f"Metric {m.get('name')} value is not numeric",
                )
            if m['value'] <= 0:
                return ValidationResult(
                    passed=False,
                    assertions_passed=assertions_passed,
                    assertions_total=assertions_total,
                    metrics_count=metrics_count,
                    benchmarks_found=benchmarks_found,
                    error_message=f"Metric {m.get('name')} has invalid value: {m['value']}",
                )
        assertions_passed += 1

        # Assertion 10b+: Exact metric values (one assertion per expected metric)
        metric_map: dict[str, float] = {}
        for m in metrics:
            metric_map[_normalize_metric_type(m["type"])] = m["value"]
        for metric, expected_value in expected_metrics.items():
            if metric not in metric_map:
                return ValidationResult(
                    passed=False,
                    assertions_passed=assertions_passed,
                    assertions_total=assertions_total,
                    metrics_count=metrics_count,
                    benchmarks_found=benchmarks_found,
                    error_message=f"Missing expected metric: {metric}",
                )
            if metric_map[metric] != expected_value:
                return ValidationResult(
                    passed=False,
                    assertions_passed=assertions_passed,
                    assertions_total=assertions_total,
                    metrics_count=metrics_count,
                    benchmarks_found=benchmarks_found,
                    error_message=f"Metric {metric} has value {metric_map[metric]}, expected {expected_value}",
                )
            assertions_passed += 1

        # Assertion 11: Has source attribution
        if 'source' not in result or 'url' not in result.get('source', {}):
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=metrics_count,
                benchmarks_found=benchmarks_found,
                error_message="Missing source or source URL",
            )
        if expected_source not in result['source']['url']:
            return ValidationResult(
                passed=False,
                assertions_passed=assertions_passed,
                assertions_total=assertions_total,
                metrics_count=metrics_count,
                benchmarks_found=benchmarks_found,
                error_message=f"Incorrect source URL: {result['source']['url']}",
            )
        assertions_passed += 1

        # All assertions passed
        return ValidationResult(
            passed=True,
            assertions_passed=assertions_passed,
            assertions_total=assertions_total,
            metrics_count=metrics_count,
            benchmarks_found=benchmarks_found,
            error_message=None,
        )

    except Exception as e:
        return ValidationResult(
            passed=False,
            assertions_passed=assertions_passed,
            assertions_total=assertions_total,
            metrics_count=metrics_count,
            benchmarks_found=benchmarks_found,
            error_message=str(e),
        )


if __name__ == "__main__":
    target_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("olmo_7b_evaluations.yaml")
    try:
        validate_evaluation_file(target_file)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ ASSERTION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}", file=sys.stderr)
        sys.exit(1)
