#!/usr/bin/env python3
import yaml

# Clean data with proper YAML escaping
clean_data = """model-index:
- name: OLMo-7B
  results:
  - task:
      type: text-generation
    dataset:
      name: Benchmarks
      type: benchmark
    metrics:
    - name: arc_challenge ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: arc_challenge
      value: 44.5
    - name: arc_easy ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: arc_easy
      value: 57.0
    - name: boolq ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: boolq
      value: 73.1
    - name: copa ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: copa
      value: 85.0
    - name: hellaswag ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: hellaswag
      value: 74.5
    - name: openbookqa ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: openbookqa
      value: 49.8
    - name: piqa ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: piqa
      value: 76.3
    - name: sciq ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: sciq
      value: 89.5
    - name: winogrande ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: winogrande
      value: 68.2
    - name: truthfulQA (MC2) ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: truthfulqa_mc2
      value: 33.9
    - name: MMLU (5 shot MC) ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: mmlu_5_shot_mc
      value: 31.5
  source:
    name: Model README
    url: https://huggingface.co/allenai/OLMo-7B"""

# Load the YAML
parsed_data = yaml.safe_load(clean_data)

# Define the benchmarks and mappings
benchmark_mappings = {
    'arc_challenge': 'ARC Challenge',
    'arc_easy': 'ARC Easy', 
    'boolq': 'BoolQ',
    'copa': 'CoPA',
    'hellaswag': 'HellaSwag',
    'openbookqa': 'OpenBookQA',
    'piqa': 'PIQA',
    'sciq': 'SciQ',
    'winogrande': 'Winogrande',
    'mmlu': 'MMLU',
    'truthfulqa': 'TruthfulQA'
}

# Filter metrics - only include benchmarks from the allowed list
filtered_metrics = []
for metric in parsed_data['model-index'][0]['results'][0]['metrics']:
    metric_type = metric['type'].lower()
    
    # Check if this metric matches our allowed benchmarks
    for benchmark_type, benchmark_name in benchmark_mappings.items():
        if benchmark_type in metric_type:
            filtered_metrics.append({
                'name': benchmark_name,
                'type': benchmark_type,
                'value': metric['value']
            })
            break

# Create the filtered YAML structure
filtered_data = {
    'model-index': [{
        'name': 'OLMo-7B',
        'results': [{
            'task': {
                'type': 'text-generation'
            },
            'dataset': {
                'name': 'Evaluation Benchmarks',
                'type': 'evaluation'
            },
            'metrics': sorted(filtered_metrics, key=lambda x: list(benchmark_mappings.keys()).index(x['type']))
        }],
        'source': {
            'name': 'Model README',
            'url': 'https://huggingface.co/allenai/OLMo-7B'
        }
    }]
}

# Save to file
with open('olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(filtered_data, f, default_flow_style=False, sort_keys=False)

print(f"Successfully filtered and saved {len(filtered_metrics)} benchmark scores to olmo_7b_evaluations.yaml")
print("\nBenchmarks included:")
for metric in sorted(filtered_metrics, key=lambda x: list(benchmark_mappings.keys()).index(x['type'])):
    print(f"  - {metric['name']}: {metric['value']}")
