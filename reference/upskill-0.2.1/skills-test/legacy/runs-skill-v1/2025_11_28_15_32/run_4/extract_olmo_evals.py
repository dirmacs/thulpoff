#!/usr/bin/env python3
"""Extract specific benchmark evaluations from OLMo-7B model card."""

import yaml
import requests
import re

# Target benchmarks to extract
TARGET_BENCHMARKS = [
    "arc_challenge",
    "arc_easy", 
    "boolq",
    "copa",
    "hellaswag",
    "openbookqa",
    "piqa",
    "sciq",
    "winogrande",
    "mmlu",
    "truthfulqa"
]

def extract_olmo_evaluations():
    """Extract evaluation scores from OLMo-7B README."""
    
    # Fetch README directly
    readme_url = "https://huggingface.co/allenai/OLMo-7B/raw/main/README.md"
    response = requests.get(readme_url)
    readme_content = response.text
    
    # Find the evaluation section for the 7B model
    eval_section = readme_content.split("## Evaluation")[1].split("And for the 1B model:")[0] if "## Evaluation" in readme_content else ""
    
    # Extract scores for each benchmark from the 7B table
    benchmark_scores = {}
    
    # Parse each line in the evaluation section
    for line in eval_section.split('\n'):
        if '|' not in line:
            continue
            
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:  # Need at least 7 columns
            continue
            
        # Skip header rows
        if 'Llama' in parts[1] or '---' in parts[1]:
            continue
            
        # Get benchmark name (first real column)
        benchmark_raw = parts[1].strip()
        
        # Get OLMo 7B score (last column before the trailing |)
        try:
            olmo_score = parts[-2].strip()
            # Parse numeric value
            if olmo_score and olmo_score.replace('.', '').isdigit():
                score = float(olmo_score)
                
                # Clean benchmark name
                benchmark = benchmark_raw.lower().strip()
                
                # Store the score
                benchmark_scores[benchmark] = score
                print(f"Found: {benchmark} = {score}")
                
        except (ValueError, IndexError) as e:
            continue
    
    # Build metrics list (only target benchmarks)
    metrics = []
    
    # Map benchmark names from README to our target format
    benchmark_mapping = {
        'arc_challenge': 'arc_challenge',
        'arc_easy': 'arc_easy',
        'boolq': 'boolq',
        'copa': 'copa',
        'hellaswag': 'hellaswag',
        'openbookqa': 'openbookqa',
        'piqa': 'piqa',
        'sciq': 'sciq',
        'winogrande': 'winogrande',
        'mmlu (5 shot mc)': 'mmlu',
        'truthfulqa (mc2)': 'truthfulqa'
    }
    
    for readme_name, target_name in benchmark_mapping.items():
        if readme_name in benchmark_scores:
            score = benchmark_scores[readme_name]
            
            # Format metric name nicely
            display_name = target_name.replace('_', ' ').title()
            if target_name == 'mmlu':
                display_name = 'MMLU (5-shot)'
            elif target_name == 'truthfulqa':
                display_name = 'TruthfulQA (MC2)'
                
            metrics.append({
                'name': display_name,
                'type': target_name,
                'value': score
            })
    
    # Build the model-index structure
    model_index = {
        'model-index': [{
            'name': 'OLMo-7B',
            'results': [{
                'task': {
                    'type': 'text-generation',
                    'name': 'Text Generation'
                },
                'dataset': {
                    'name': 'Common Benchmarks',
                    'type': 'evaluation-suite'
                },
                'metrics': metrics,
                'source': {
                    'name': 'OLMo Model Card',
                    'url': 'https://huggingface.co/allenai/OLMo-7B'
                }
            }]
        }]
    }
    
    return model_index

def main():
    """Main execution."""
    print("Extracting evaluation scores from allenai/OLMo-7B...\n")
    
    evaluations = extract_olmo_evaluations()
    
    # Save to YAML file
    output_file = "olmo_7b_evaluations.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(evaluations, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"\n✓ Saved {len(evaluations['model-index'][0]['results'][0]['metrics'])} evaluation metrics to {output_file}")
    print("\nExtracted benchmarks:")
    for metric in evaluations['model-index'][0]['results'][0]['metrics']:
        print(f"  - {metric['name']}: {metric['value']}")
    
    # Display the YAML content
    print(f"\n--- {output_file} ---")
    with open(output_file, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    main()
