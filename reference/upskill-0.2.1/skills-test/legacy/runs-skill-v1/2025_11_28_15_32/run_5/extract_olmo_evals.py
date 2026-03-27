#!/usr/bin/env python3
"""
Extract specific evaluation benchmarks from OLMo-7B model card
"""
import yaml
from huggingface_hub import HfApi

# Benchmarks to extract
REQUIRED_BENCHMARKS = [
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

# Manual extraction from the README table for OLMo 7B column
OLMO_7B_SCORES = {
    'arc_challenge': 48.5,
    'arc_easy': 65.4,
    'boolq': 73.4,
    'copa': 90.0,
    'hellaswag': 76.4,
    'openbookqa': 50.2,
    'piqa': 78.4,
    'sciq': 93.8,
    'winogrande': 67.9,
    'mmlu': 28.3,  # MMLU (5 shot MC)
    'truthfulqa': 36.0  # truthfulQA (MC2)
}

def create_model_index():
    """Create model-index YAML structure with filtered evaluations"""
    
    metrics = []
    for benchmark in REQUIRED_BENCHMARKS:
        if benchmark in OLMO_7B_SCORES:
            # Create proper metric name
            if benchmark == 'mmlu':
                metric_name = 'MMLU (5 shot MC)'
            elif benchmark == 'truthfulqa':
                metric_name = 'truthfulQA (MC2)'
            else:
                metric_name = benchmark
            
            metrics.append({
                'name': metric_name,
                'type': benchmark.lower(),
                'value': OLMO_7B_SCORES[benchmark]
            })
    
    model_index = [{
        'name': 'OLMo-7B',
        'results': [{
            'task': {
                'type': 'text-generation'
            },
            'dataset': {
                'name': 'Core Benchmarks',
                'type': 'benchmark'
            },
            'metrics': metrics,
            'source': {
                'name': 'OLMo Technical Report',
                'url': 'https://huggingface.co/allenai/OLMo-7B'
            }
        }]
    }]
    
    return {'model-index': model_index}

def main():
    """Generate and save the YAML file"""
    model_index = create_model_index()
    
    output_file = 'olmo_7b_evaluations.yaml'
    
    with open(output_file, 'w') as f:
        yaml.dump(model_index, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Successfully created {output_file}")
    print(f"✓ Included {len(OLMO_7B_SCORES)} benchmark scores")
    print(f"\nBenchmarks included:")
    for benchmark, score in OLMO_7B_SCORES.items():
        print(f"  - {benchmark}: {score}")

if __name__ == '__main__':
    main()
