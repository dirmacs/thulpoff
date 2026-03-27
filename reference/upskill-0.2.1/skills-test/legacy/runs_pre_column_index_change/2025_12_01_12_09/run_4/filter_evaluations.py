import yaml

# The extracted evaluation data
evaluation_data = {
    'model-index': [
        {
            'name': 'OLMo-7B',
            'results': [
                {
                    'task': {
                        'type': 'text-generation'
                    },
                    'dataset': {
                        'name': 'Benchmarks',
                        'type': 'benchmark'
                    },
                    'metrics': [],
                    'source': {
                        'name': 'Model README',
                        'url': 'https://huggingface.co/allenai/OLMo-7B'
                    }
                }
            ]
        }
    ]
}

# Benchmarks to include
required_benchmarks = {
    'arc_challenge',
    'arc_easy',
    'boolq',
    'copa',
    'hellaswag',
    'openbookqa',
    'piqa',
    'sciq',
    'winogrande',
    'mmlu',
    'truthfulqa'
}

# Raw metrics from extraction
metrics_raw = [
    {'name': 'arc_challenge', 'type': 'arc_challenge', 'value': 48.5},
    {'name': 'arc_easy', 'type': 'arc_easy', 'value': 65.4},
    {'name': 'boolq', 'type': 'boolq', 'value': 73.4},
    {'name': 'copa', 'type': 'copa', 'value': 90.0},
    {'name': 'hellaswag', 'type': 'hellaswag', 'value': 76.4},
    {'name': 'openbookqa', 'type': 'openbookqa', 'value': 50.2},
    {'name': 'piqa', 'type': 'piqa', 'value': 78.4},
    {'name': 'sciq', 'type': 'sciq', 'value': 93.8},
    {'name': 'winogrande', 'type': 'winogrande', 'value': 67.9},
    {'name': 'truthfulQA (MC2)', 'type': 'truthfulqa_(mc2)', 'value': 36.0},
    {'name': 'MMLU (5 shot MC)', 'type': 'mmlu_(5_shot_mc)', 'value': 28.3},
]

# Filter metrics
filtered_metrics = []
for metric in metrics_raw:
    metric_type = metric['type'].lower()
    # Check if this metric type matches any of the required benchmarks
    if any(bench in metric_type for bench in required_benchmarks):
        filtered_metrics.append(metric)

# Update the evaluation data
evaluation_data['model-index'][0]['results'][0]['metrics'] = filtered_metrics

# Write to YAML file
with open('/home/ssmith/source/skills-test/olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(evaluation_data, f, default_flow_style=False, sort_keys=False)

print("✓ Saved filtered evaluations to olmo_7b_evaluations.yaml")
print(f"✓ Included {len(filtered_metrics)} benchmarks from the required list")
print("\nMetrics included:")
for metric in filtered_metrics:
    print(f"  - {metric['name']}: {metric['value']}")
