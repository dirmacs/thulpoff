import yaml

# Define the allowed benchmark types
allowed_benchmarks = {
    'arc_challenge', 'arc_easy', 'boolq', 'copa', 'hellaswag',
    'openbookqa', 'piqa', 'sciq', 'winogrande', 'mmlu', 'truthfulqa'
}

# The extracted YAML data
yaml_data = """
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
data = yaml.safe_load(yaml_data)

# Filter metrics
filtered_metrics = []
for metric in data['model-index'][0]['results'][0]['metrics']:
    metric_type = metric['type'].lower().replace('_', '').replace('(', '').replace(')', '').replace(' ', '')
    
    # Check if this metric matches any of our allowed benchmarks
    for allowed in allowed_benchmarks:
        allowed_normalized = allowed.replace('_', '')
        if allowed_normalized in metric_type:
            # Clean up the metric name and type
            if 'truthful' in metric_type:
                metric['name'] = 'truthfulqa'
                metric['type'] = 'truthfulqa'
            elif 'mmlu' in metric_type:
                metric['name'] = 'mmlu'
                metric['type'] = 'mmlu'
            
            filtered_metrics.append(metric)
            break

# Update the data with filtered metrics
data['model-index'][0]['results'][0]['metrics'] = filtered_metrics

# Write to file
with open('olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print("✓ Successfully created olmo_7b_evaluations.yaml")
print(f"✓ Included {len(filtered_metrics)} benchmark scores")
print("\nFiltered benchmarks:")
for metric in filtered_metrics:
    print(f"  - {metric['name']}: {metric['value']}")
