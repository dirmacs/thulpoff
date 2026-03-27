import yaml

# Define the allowed benchmarks
allowed_benchmarks = {
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

# The extracted YAML data
data = {
    'model-index': [{
        'name': 'OLMo-7B',
        'results': [{
            'task': {
                'type': 'text-generation'
            },
            'dataset': {
                'name': 'Benchmarks',
                'type': 'benchmark'
            },
            'metrics': [
                {'name': 'arc_challenge', 'type': 'arc_challenge', 'value': 48.5},
                {'name': 'arc_easy', 'type': 'arc_easy', 'value': 65.4},
                {'name': 'boolq', 'type': 'boolq', 'value': 73.4},
                {'name': 'copa', 'type': 'copa', 'value': 90.0},
                {'name': 'hellaswag', 'type': 'hellaswag', 'value': 76.4},
                {'name': 'openbookqa', 'type': 'openbookqa', 'value': 50.2},
                {'name': 'piqa', 'type': 'piqa', 'value': 78.4},
                {'name': 'sciq', 'type': 'sciq', 'value': 93.8},
                {'name': 'winogrande', 'type': 'winogrande', 'value': 67.9},
                {'name': '**Core tasks average**', 'type': '**core_tasks_average**', 'value': 71.6},
                {'name': 'truthfulQA (MC2)', 'type': 'truthfulqa_(mc2)', 'value': 36.0},
                {'name': 'MMLU (5 shot MC)', 'type': 'mmlu_(5_shot_mc)', 'value': 28.3},
                {'name': '**Full average**', 'type': '**full_average**', 'value': 59.8}
            ],
            'source': {
                'name': 'Model README',
                'url': 'https://huggingface.co/allenai/OLMo-7B'
            }
        }]
    }]
}

# Filter metrics to only include allowed benchmarks
filtered_metrics = []
for metric in data['model-index'][0]['results'][0]['metrics']:
    metric_type = metric['type'].lower()
    # Remove markdown formatting and parentheses for matching
    metric_type_clean = metric_type.replace('**', '').replace('_(mc2)', '').replace('_(5_shot_mc)', '')
    
    # Check if the clean metric type starts with any allowed benchmark
    for allowed in allowed_benchmarks:
        if metric_type_clean.startswith(allowed):
            # Normalize the type field for consistency
            if 'truthful' in metric_type_clean:
                metric['type'] = 'truthfulqa'
                metric['name'] = 'TruthfulQA'
            elif 'mmlu' in metric_type_clean:
                metric['type'] = 'mmlu'
                metric['name'] = 'MMLU'
            filtered_metrics.append(metric)
            break

# Update the data with filtered metrics
data['model-index'][0]['results'][0]['metrics'] = filtered_metrics

# Write to YAML file
with open('/home/ssmith/source/skills-test/olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print("Filtered evaluation data saved to olmo_7b_evaluations.yaml")
print(f"Included {len(filtered_metrics)} benchmarks out of 13 total metrics")
