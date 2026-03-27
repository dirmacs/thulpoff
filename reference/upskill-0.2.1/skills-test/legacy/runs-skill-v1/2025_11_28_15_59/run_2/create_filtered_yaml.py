import yaml
import sys

# Raw evaluation data from the OLMo 7B README extraction
raw_data = {
    "model-index": [
        {
            "name": "OLMo-7B",
            "results": [
                {
                    "task": {"type": "text-generation"},
                    "dataset": {"name": "Benchmarks", "type": "benchmark"},
                    "metrics": [
                        {"name": "arc_challenge", "type": "arc_challenge", "value": 48.5},
                        {"name": "arc_easy", "type": "arc_easy", "value": 65.4},
                        {"name": "boolq", "type": "boolq", "value": 73.4},
                        {"name": "copa", "type": "copa", "value": 90.0},
                        {"name": "hellaswag", "type": "hellaswag", "value": 76.4},
                        {"name": "openbookqa", "type": "openbookqa", "value": 50.2},
                        {"name": "piqa", "type": "piqa", "value": 78.4},
                        {"name": "sciq", "type": "sciq", "value": 93.8},
                        {"name": "winogrande", "type": "winogrande", "value": 67.9},
                        {"name": "MMLU", "type": "mmlu", "value": 28.3},
                        {"name": "TruthfulQA", "type": "truthfulqa", "value": 36.0}
                    ],
                    "source": {
                        "name": "Model README", 
                        "url": "https://huggingface.co/allenai/OLMo-7B"
                    }
                }
            ]
        }
    ]
}

# Filter to only include the specified benchmark types
allowed_benchmarks = {
    'arc_challenge', 'arc_easy', 'boolq', 'copa', 'hellaswag',
    'openbookqa', 'piqa', 'sciq', 'winogrande', 'mmlu', 'truthfulqa'
}

# Create filtered structure
filtered_data = {
    "model-index": [
        {
            "name": "OLMo-7B",
            "results": [
                {
                    "task": {"type": "text-generation"},
                    "dataset": {"name": "Benchmarks", "type": "benchmark"},
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

# Filter metrics based on allowed benchmarks and normalize types
for metric in raw_data["model-index"][0]["results"][0]["metrics"]:
    metric_type = metric["type"].lower().replace("(mc2)", "").replace("(", "_").replace(")", "")
    metric_name = metric["name"].lower()
    
    if metric_type in allowed_benchmarks or metric_name in allowed_benchmarks:
        # Normalize to standard types
        if metric_type.startswith("truthfulqa"):
            metric_type = "truthfulqa"
        elif metric_type.startswith("mmlu"):
            metric_type = "mmlu"
        
        normalized_metric = {
            "name": metric["name"],
            "type": metric_type,
            "value": metric["value"]
        }
        filtered_data["model-index"][0]["results"][0]["metrics"].append(normalized_metric)

# Sort metrics by name for consistency
filtered_data["model-index"][0]["results"][0]["metrics"].sort(key=lambda x: x["name"])

# Write to YAML file
with open("olmo_7b_evaluations.yaml", "w") as f:
    yaml.dump(filtered_data, f, default_flow_style=False, sort_keys=False)

print("Created olmo_7b_evaluations.yaml with filtered evaluation benchmarks:")
for metric in filtered_data["model-index"][0]["results"][0]["metrics"]:
    print(f"  - {metric['name']}: {metric['value']}")
