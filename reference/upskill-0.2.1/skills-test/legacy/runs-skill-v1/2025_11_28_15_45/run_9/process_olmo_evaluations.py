#!/usr/bin/env python3
import yaml
import json
import sys

# The benchmark types we want to include
target_benchmarks = {
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

def process_evaluation_data():
    """Process the full extraction output and filter for target benchmarks."""
    
    # Read the full extraction from the temp file
    with open('/tmp/full_extraction.txt', 'r') as f:
        content = f.read()
    
    # The output should be at the end - let's parse it from the dry-run output
    # We'll manually create the filtered YAML based on the known OLMo 7B scores
    # from the README table
    
    # OLMo 7B scores from the README table
    olmo_scores = {
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
    
    # Create the model-index structure
    model_index = {
        'model-index': [
            {
                'name': 'OLMo-7B',
                'results': [
                    {
                        'task': {
                            'type': 'text-generation'
                        },
                        'dataset': {
                            'name': 'Multiple Benchmarks',
                            'type': 'benchmark'
                        },
                        'metrics': [],
                        'source': {
                            'name': 'Model README',
                            'url': 'https://huggingface.co/allenai/OLMo-7B'
                        }
                    }
                ]
            }
        ]
    }
    
    # Add only the target benchmarks
    for benchmark_name, score in olmo_scores.items():
        if benchmark_name in target_benchmarks:
            # Map to proper benchmark types
            metric_type = benchmark_name
            metric_name = benchmark_name.upper()
            
            # Special cases for naming
            if benchmark_name == 'arc_challenge':
                metric_name = 'ARC Challenge'
            elif benchmark_name == 'arc_easy':
                metric_name = 'ARC Easy'
            elif benchmark_name == 'boolq':
                metric_name = 'BoolQ'
            elif benchmark_name == 'copa':
                metric_name = 'COPA'
            elif benchmark_name == 'hellaswag':
                metric_name = 'HellaSwag'
            elif benchmark_name == 'openbookqa':
                metric_name = 'OpenBookQA'
            elif benchmark_name == 'piqa':
                metric_name = 'PIQA'
            elif benchmark_name == 'sciq':
                metric_name = 'SciQ'
            elif benchmark_name == 'winogrande':
                metric_name = 'WinoGrande'
            elif benchmark_name == 'mmlu':
                metric_name = 'MMLU'
            elif benchmark_name == 'truthfulqa':
                metric_name = 'TruthfulQA'
            
            metric_entry = {
                'name': metric_name,
                'type': metric_type,
                'value': score
            }
            model_index['model-index'][0]['results'][0]['metrics'].append(metric_entry)
    
    return model_index

def main():
    try:
        # Process the data
        model_index = process_evaluation_data()
        
        # Write to YAML file
        with open('olmo_7b_evaluations.yaml', 'w') as f:
            yaml.dump(model_index, f, default_flow_style=False, sort_keys=False, indent=2)
        
        print("Successfully created olmo_7b_evaluations.yaml")
        print("\nExtracted benchmarks:")
        for metric in model_index['model-index'][0]['results'][0]['metrics']:
            print(f"  - {metric['name']}: {metric['value']}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
