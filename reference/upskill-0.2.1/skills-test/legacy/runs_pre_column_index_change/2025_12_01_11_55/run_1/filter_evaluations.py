#!/usr/bin/env python3
import yaml
import re

# Raw YAML data from the extraction
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

# Filter benchmarks
allowed_benchmarks = {
    'arc_challenge', 'arc_easy', 'boolq', 'copa', 'hellaswag', 
    'openbookqa', 'piqa', 'sciq', 'winogrande', 'mmlu', 'truthfulqa'
}

# Filter metrics
filtered_metrics = []
for metric in data['model-index'][0]['results'][0]['metrics']:
    # Clean up the metric name by removing markdown and extra text
    clean_name = re.sub(r'\*\*|\(.*\)', '', metric['name']).strip().lower()
    clean_type = re.sub(r'\*\*|\(.*\)', '', metric['type']).strip().lower()
    
    # Check if this is one of our allowed benchmarks
    if clean_name in allowed_benchmarks or clean_type in allowed_benchmarks:
        # Normalize the benchmark name for consistency
        if clean_name in allowed_benchmarks:
            normalized_name = clean_name
        else:
            normalized_name = clean_type
            
        # Create clean metric entry
        clean_metric = {
            'name': normalized_name.upper(),
            'type': normalized_name,
            'value': metric['value']
        }
        filtered_metrics.append(clean_metric)

# Update the data with filtered metrics
data['model-index'][0]['results'][0]['metrics'] = filtered_metrics

# Save to file
with open('olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print("Filtered evaluations saved to olmo_7b_evaluations.yaml")
print(f"Included benchmarks: {[m['type'] for m in filtered_metrics]}")
