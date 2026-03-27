#!/usr/bin/env python3
import yaml

# Original extracted data
data = """model-index:
- name: OLMo-7B
  results:
  - task:
      type: text-generation
    dataset:
      name: Benchmarks
      type: benchmark
    metrics:
    - name: '[OLMo 1B](https://huggingface.co/allenai/OLMo-1B) (Layers)'
      type: '[olmo_1b](https://huggingface.co/allenai/olmo-1b)'
      value: 16.0
    - name: '[OLMo 7B](https://huggingface.co/allenai/OLMo-7B) (Layers)'
      type: '[olmo_7b](https://huggingface.co/allenai/olmo-7b)'
      value: 32.0
    - name: '[OLMo 7B Twin 2T](https://huggingface.co/allenai/OLMo-7B-Twin-2T) (Layers)'
      type: '[olmo_7b_twin_2t](https://huggingface.co/allenai/olmo-7b-twin-2t)'
      value: 32.0
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
    - name: '**Core tasks average** ([Llama 7B](https://arxiv.org/abs/2302.13971))'
      type: '**core_tasks_average**'
      value: 68.7
    - name: truthfulQA (MC2) ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: truthfulqa_(mc2)
      value: 33.9
    - name: MMLU (5 shot MC) ([Llama 7B](https://https://arxiv.org/abs/2302.13971))
      type: mmlu_(5_shot_mc)
      value: 31.5
    - name: '**Full average** ([Llama 7B](https://arxiv.org/abs/2302.13971))
      type: '**full_average**'
      value: 57.8
    - name: arc_challenge (random)
      type: arc_challenge
      value: 25.0
    - name: arc_easy (random)
      type: arc_easy
      value: 25.0
    - name: boolq (random)
      type: boolq
      value: 50.0
    - name: copa (random)
      type: copa
      value: 50.0
    - name: hellaswag (random)
      type: hellaswag
      value: 25.0
    - name: openbookqa (random)
      type: openbookqa
      value: 25.0
    - name: piqa (random)
      type: piqa
      value: 50.0
    - name: sciq (random)
      type: sciq
      value: 25.0
    - name: winogrande (random)
      type: winogrande
      value: 50.0
    - name: Average (random)
      type: average
      value: 36.11
    - name: d_model
      type: d_model
      value: 4096.0
    - name: num heads
      type: num_heads
      value: 32.0
    - name: num layers
      type: num_layers
      value: 32.0
    - name: sequence length
      type: sequence_length
      value: 2048.0
    - name: batch size (instances)
      type: batch_size_(instances)
      value: 2160.0
    - name: 1B (Peak LR)
      type: 1b
      value: 0.0004
    - name: 7B (Peak LR)
      type: 7b
      value: 0.0003
    - name: warmup steps
      type: warmup_steps
      value: 5000.0
    - name: peak LR
      type: peak_lr
      value: 0.0003
    - name: minimum LR
      type: minimum_lr
      value: 3.0e-05
    - name: weight decay
      type: weight_decay
      value: 0.1
    - name: beta1
      type: beta1
      value: 0.9
    - name: beta2
      type: beta2
      value: 0.95
    - name: epsilon
      type: epsilon
      value: 1.0e-05
    - name: "OLMo 7B (Carbon Intensity (kg CO\u2082e/KWh))"
      type: olmo_7b
      value: 0.656
  source:
    name: Model README
    url: https://huggingface.co/allenai/OLMo-7B"""

# Load the YAML
parsed_data = yaml.safe_load(data)

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

# Filter metrics - only include non-random benchmarks from the allowed list
filtered_metrics = []
for metric in parsed_data['model-index'][0]['results'][0]['metrics']:
    metric_type = metric['type'].lower()
    metric_name = metric['name'].lower()
    
    # Skip random baseline scores and architectural specs
    if 'random' in metric_name or any(x in metric_type for x in ['olmo_', '1b', '7b', 'd_model', 'num_', 'sequence', 'batch', 'warmup', 'peak', 'minimum', 'weight', 'beta', 'epsilon', 'carbon', 'average', 'core']):
        continue
    
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
            'metrics': filtered_metrics
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
for metric in filtered_metrics:
    print(f"  - {metric['name']}: {metric['value']}")
