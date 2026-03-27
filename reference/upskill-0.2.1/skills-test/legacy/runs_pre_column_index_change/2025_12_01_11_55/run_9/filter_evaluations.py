#!/usr/bin/env python3
import yaml
import re

# Original data from the extraction
raw_yaml = """
model-index:
- name: OLMo-7B
  results:
  - task:
      type: text-generation
    dataset:
      name: Benchmarks
      type: benchmark
    metrics:
    - name: arc_challenge
      type: arc_challenge
      value: 48.5
    - name: arc_easy
      type: arc_easy
      value: 65.4
    - name: boolq
      type: boolq
      value: 73.4
    - name: copa
      type: copa
      value: 90.0
    - name: hellaswag
      type: hellaswag
      value: 76.4
    - name: openbookqa
      type: openbookqa
      value: 50.2
    - name: piqa
      type: piqa
      value: 78.4
    - name: sciq
      type: sciq
      value: 93.8
    - name: winogrande
      type: winogrande
      value: 67.9
    - name: '**Core tasks average**'
      type: '**core_tasks_average**'
      value: 71.6
    - name: truthfulQA (MC2)
      type: truthfulqa_(mc2)
      value: 36.0
    - name: MMLU (5 shot MC)
      type: mmlu_(5_shot_mc)
      value: 28.3
    - name: '**Full average**'
      type: '**full_average**'
      value: 59.8
    source:
      name: Model README
      url: https://huggingface.co/allenai/OLMo-7B
"""

# Parse the YAML
data = yaml.safe_load(raw_yaml)

# Required benchmarks
required_benchmarks = [
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
]

# Filter metrics to only include required benchmarks
filtered_metrics = []
for metric in data['model-index'][0]['results'][0]['metrics']:
    metric_name = metric['name'].lower()
    metric_type = metric['type'].lower()
    
    # Check if this benchmark should be included
    include = False
    for benchmark in required_benchmarks:
        if benchmark in metric_name or benchmark in metric_type:
            # Normalize the metric to match the required format
            metric['name'] = benchmark
            metric['type'] = benchmark
            include = True
            break
    
    if include:
        filtered_metrics.append(metric)

# Update the data with filtered metrics
data['model-index'][0]['results'][0]['metrics'] = filtered_metrics

# Update source attribution
data['model-index'][0]['results'][0]['source'] = {
    'name': 'Model README',
    'url': 'https://huggingface.co/allenai/OLMo-7B'
}

# Write to YAML file
with open('olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print("Filtered evaluations saved to olmo_7b_evaluations.yaml")
print("\nContent:")
print(yaml.dump(data, default_flow_style=False, sort_keys=False))
