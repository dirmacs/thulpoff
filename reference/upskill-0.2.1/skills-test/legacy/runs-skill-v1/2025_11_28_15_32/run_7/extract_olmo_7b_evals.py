import yaml
import sys

# Define the benchmarks we want and their exact scores from the OLMo 7B column
# Based on the table in the README
benchmarks = {
    "arc_challenge": 48.5,
    "arc_easy": 65.4,
    "boolq": 73.4,
    "copa": 90.0,
    "hellaswag": 76.4,
    "openbookqa": 50.2,
    "piqa": 78.4,
    "sciq": 93.8,
    "winogrande": 67.9,
    "mmlu": 28.3,  # MMLU (5 shot MC)
    "truthfulqa": 36.0  # truthfulQA (MC2)
}

# Create the model-index structure
model_index = {
    "model-index": [
        {
            "name": "OLMo-7B",
            "results": [
                {
                    "task": {
                        "type": "text-generation"
                    },
                    "dataset": {
                        "name": "Core Benchmarks",
                        "type": "benchmark"
                    },
                    "metrics": [],
                    "source": {
                        "name": "Model README",
                        "url": "https://huggingface.co/allenai/OLMo-7B"
                    }
                }
            ]
        }
    ]
}

# Add each benchmark as a metric
for benchmark_name, value in benchmarks.items():
    # Create metric name mapping
    metric_display_names = {
        "arc_challenge": "ARC Challenge",
        "arc_easy": "ARC Easy",
        "boolq": "BoolQ",
        "copa": "COPA",
        "hellaswag": "HellaSwag",
        "openbookqa": "OpenBookQA",
        "piqa": "PIQA",
        "sciq": "SciQ",
        "winogrande": "Winogrande",
        "mmlu": "MMLU (5-shot MC)",
        "truthfulqa": "TruthfulQA (MC2)"
    }
    
    metric = {
        "name": metric_display_names[benchmark_name],
        "type": benchmark_name,
        "value": value
    }
    model_index["model-index"][0]["results"][0]["metrics"].append(metric)

# Write to YAML file
output_file = "olmo_7b_evaluations.yaml"
with open(output_file, 'w') as f:
    yaml.dump(model_index, f, default_flow_style=False, sort_keys=False)

print(f"✓ Successfully extracted evaluations to {output_file}")
print(f"\nExtracted {len(benchmarks)} benchmarks:")
for benchmark, value in benchmarks.items():
    print(f"  - {benchmark}: {value}")
