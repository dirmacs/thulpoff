#!/usr/bin/env python3
"""Extract OLMo-7B evaluation scores and save to YAML."""

import yaml
import sys

# Define the benchmarks we want to extract
TARGET_BENCHMARKS = {
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

# OLMo-7B scores from the model card (from the comparison table)
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
    'mmlu': 28.3,  # from "MMLU (5 shot MC)" row
    'truthfulqa': 36.0  # from "truthfulQA (MC2)" row
}

def create_model_index():
    """Create model-index YAML structure with OLMo-7B scores."""
    
    # Build metrics list
    metrics = []
    for benchmark in sorted(TARGET_BENCHMARKS):
        if benchmark in OLMO_7B_SCORES:
            # Clean up metric names
            metric_name = benchmark.replace('_', ' ').title()
            if benchmark == 'mmlu':
                metric_name = 'MMLU'
            elif benchmark == 'truthfulqa':
                metric_name = 'TruthfulQA'
            
            metrics.append({
                'name': metric_name,
                'type': benchmark,
                'value': OLMO_7B_SCORES[benchmark]
            })
    
    # Create model-index structure
    model_index = {
        'model-index': [{
            'name': 'OLMo-7B',
            'results': [{
                'task': {
                    'type': 'text-generation',
                    'name': 'Text Generation'
                },
                'dataset': {
                    'name': 'Core Language Benchmarks',
                    'type': 'benchmark'
                },
                'metrics': metrics,
                'source': {
                    'name': 'Model README',
                    'url': 'https://huggingface.co/allenai/OLMo-7B'
                }
            }]
        }]
    }
    
    return model_index

def main():
    """Extract evaluations and save to YAML file."""
    output_file = 'olmo_7b_evaluations.yaml'
    
    # Create the model-index structure
    model_index = create_model_index()
    
    # Save to YAML file
    with open(output_file, 'w') as f:
        yaml.dump(model_index, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Successfully extracted {len(TARGET_BENCHMARKS)} benchmark scores")
    print(f"✓ Saved to {output_file}")
    print(f"\nExtracted benchmarks:")
    for metric in model_index['model-index'][0]['results'][0]['metrics']:
        print(f"  - {metric['name']}: {metric['value']}")

if __name__ == '__main__':
    main()
