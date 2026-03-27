#!/usr/bin/env python3
"""
Extract evaluation benchmark scores for allenai/OLMo-7B
Filters for specific benchmarks and excludes non-evaluation data
"""
import yaml
from typing import Dict, List

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

# Manual extraction from the README comparison table
# These are the scores for OLMo 7B from the evaluation table
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

def create_model_index() -> Dict:
    """Create model-index YAML structure with filtered evaluation results."""
    
    metrics = []
    for benchmark_name in sorted(TARGET_BENCHMARKS):
        if benchmark_name in OLMO_7B_SCORES:
            # Map benchmark names to proper display names
            display_names = {
                'arc_challenge': 'ARC Challenge',
                'arc_easy': 'ARC Easy',
                'boolq': 'BoolQ',
                'copa': 'COPA',
                'hellaswag': 'HellaSwag',
                'openbookqa': 'OpenBookQA',
                'piqa': 'PIQA',
                'sciq': 'SciQ',
                'winogrande': 'Winogrande',
                'mmlu': 'MMLU (5 shot)',
                'truthfulqa': 'TruthfulQA (MC2)'
            }
            
            metric = {
                'name': display_names.get(benchmark_name, benchmark_name),
                'type': benchmark_name,
                'value': OLMO_7B_SCORES[benchmark_name]
            }
            metrics.append(metric)
    
    model_index = {
        'model-index': [{
            'name': 'OLMo-7B',
            'results': [{
                'task': {
                    'type': 'text-generation'
                },
                'dataset': {
                    'name': 'Standard Benchmarks',
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
    """Generate and save the filtered evaluation YAML."""
    model_index = create_model_index()
    
    # Save to file
    output_file = 'olmo_7b_evaluations.yaml'
    with open(output_file, 'w') as f:
        yaml.dump(model_index, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"✅ Successfully extracted {len(OLMO_7B_SCORES)} benchmark scores")
    print(f"📝 Saved to: {output_file}")
    print(f"\nBenchmarks included:")
    for benchmark in sorted(TARGET_BENCHMARKS):
        if benchmark in OLMO_7B_SCORES:
            score = OLMO_7B_SCORES[benchmark]
            print(f"  • {benchmark}: {score}")
    
    print(f"\n📄 Preview of YAML structure:")
    print("─" * 60)
    print(yaml.dump(model_index, default_flow_style=False, sort_keys=False))

if __name__ == '__main__':
    main()
