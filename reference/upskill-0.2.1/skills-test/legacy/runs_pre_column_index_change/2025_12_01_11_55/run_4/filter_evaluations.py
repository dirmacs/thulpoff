import yaml
import re

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

# Original extracted data
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

# Filter metrics to only include required benchmarks
filtered_metrics = []
for metric in data['model-index'][0]['results'][0]['metrics']:
    metric_name = metric['name'].lower()
    metric_type = metric['type'].lower()
    
    # Check if this metric matches any required benchmark
    for benchmark in required_benchmarks:
        if benchmark in metric_name or benchmark in metric_type:
            # Clean up the metric name and type for the final output
            clean_metric = {
                'name': benchmark,
                'type': benchmark,
                'value': metric['value']
            }
            filtered_metrics.append(clean_metric)
            break

# Create the filtered result
filtered_result = {
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
            'metrics': filtered_metrics,
            'source': {
                'name': 'Model README',
                'url': 'https://huggingface.co/allenai/OLMo-7B'
            }
        }]
    }]
}

# Save to YAML file
with open('olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(filtered_result, f, default_flow_style=False, sort_keys=False)

print("Filtered evaluations saved to olmo_7b_evaluations.yaml")
print(f"Included {len(filtered_metrics)} benchmarks:")
for metric in filtered_metrics:
    print(f"  - {metric['name']}: {metric['value']}")
