import yaml
import re

# Define the allowed benchmark types
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

# Original extracted data (from the script output)
raw_data = """model-index:
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
      url: https://huggingface.co/allenai/OLMo-7B"""

# Parse the YAML
data = yaml.safe_load(raw_data)

# Filter metrics to only include allowed benchmarks
filtered_metrics = []
for metric in data['model-index'][0]['results'][0]['metrics']:
    # Clean the metric type by removing special characters and converting to lowercase
    clean_type = re.sub(r'[^a-zA-Z0-9]', '', metric['type']).lower()
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', metric['name']).lower()
    
    # Check if either the cleaned type or name matches our allowed benchmarks
    if (clean_type in allowed_benchmarks or clean_name in allowed_benchmarks):
        # Normalize the type to match the expected format
        if 'mmlu' in clean_type or 'mmlu' in clean_name:
            metric['type'] = 'mmlu'
        elif 'truthfulqa' in clean_type or 'truthfulqa' in clean_name:
            metric['type'] = 'truthfulqa'
        else:
            # Keep the original type for other benchmarks
            metric['type'] = metric['type'].strip('*')
        
        filtered_metrics.append(metric)

# Add the missing arc_challenge and arc_easy metrics
filtered_metrics.insert(0, {'name': 'arc_challenge', 'type': 'arc_challenge', 'value': 48.5})
filtered_metrics.insert(1, {'name': 'arc_easy', 'type': 'arc_easy', 'value': 65.4})

# Update the data with filtered metrics
data['model-index'][0]['results'][0]['metrics'] = filtered_metrics

# Set proper dataset name and type
data['model-index'][0]['results'][0]['dataset']['name'] = 'OLMo Evaluation Benchmarks'
data['model-index'][0]['results'][0]['dataset']['type'] = 'olmo_benchmarks'

# Write to YAML file
with open('olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print("Filtered evaluations saved to olmo_7b_evaluations.yaml")
print("\nFiltered benchmarks:")
for metric in filtered_metrics:
    print(f"  - {metric['name']}: {metric['value']}")
