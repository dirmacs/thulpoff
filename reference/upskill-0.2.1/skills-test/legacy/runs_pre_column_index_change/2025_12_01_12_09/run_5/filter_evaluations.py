#!/usr/bin/env python3
"""Filter OLMo 7B evaluations and save to YAML."""

import yaml

# Original extracted data
data = {
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
                        {'name': '**Full average**', 'type': '**full_average**', 'value': 59.8},
                    ],
                    'source': {
                        'name': 'Model README',
                        'url': 'https://huggingface.co/allenai/OLMo-7B'
                    }
                }
            ]
        }
    ]
}

# Allowed benchmark types
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
    'mmlu_(5_shot_mc)',  # Maps to 'mmlu'
    'truthfulqa_(mc2)',  # Maps to 'truthfulqa'
}

# Filter metrics
filtered_metrics = []
for metric in data['model-index'][0]['results'][0]['metrics']:
    metric_type = metric['type']
    # Map normalized types
    normalized_type = metric_type.lower().replace(' ', '_')
    
    # Check if it's in allowed list
    if metric_type in allowed_benchmarks or normalized_type in allowed_benchmarks:
        filtered_metrics.append(metric)

# Update the data with filtered metrics
data['model-index'][0]['results'][0]['metrics'] = filtered_metrics

# Save to YAML file
output_file = '/home/ssmith/source/skills-test/olmo_7b_evaluations.yaml'
with open(output_file, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"✓ Saved filtered evaluations to {output_file}")
print(f"✓ Included {len(filtered_metrics)} benchmark scores")
print("\nGenerated YAML content:")
with open(output_file, 'r') as f:
    print(f.read())
