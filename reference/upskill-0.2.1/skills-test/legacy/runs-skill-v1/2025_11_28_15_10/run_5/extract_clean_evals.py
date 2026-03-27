#!/usr/bin/env python3

import yaml
import re

def create_clean_evaluations():
    """Create clean evaluation data for OLMo-7B based on the README table"""
    
    # These are the actual OLMo-7B scores from the README table
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
        'mmlu': 28.3,  # MMLU (5 shot MC) from the table
        'truthfulqa': 36.0  # truthfulQA (MC2) from the table
    }
    
    # Create the metrics list
    metrics = []
    for benchmark, score in olmo_scores.items():
        metrics.append({
            'name': benchmark,
            'type': benchmark,
            'value': score
        })
    
    # Create the model-index structure
    model_index = {
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
    """Main function to create and save clean evaluations"""
    try:
        # Create clean evaluation data
        clean_data = create_clean_evaluations()
        
        # Save to YAML file
        output_file = 'olmo_7b_evaluations.yaml'
        with open(output_file, 'w') as f:
            yaml.dump(clean_data, f, default_flow_style=False, sort_keys=False, indent=2)
        
        print(f"Successfully saved clean evaluations to {output_file}")
        
        # Display the saved content
        print("\nSaved YAML content:")
        with open(output_file, 'r') as f:
            print(f.read())
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
