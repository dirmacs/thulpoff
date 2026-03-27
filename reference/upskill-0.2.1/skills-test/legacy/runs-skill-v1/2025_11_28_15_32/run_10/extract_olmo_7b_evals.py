#!/usr/bin/env python3
"""
Extract specific evaluation benchmarks from allenai/OLMo-7B model card.
"""

import yaml
from huggingface_hub import hf_hub_download, HfApi
import re

# Benchmarks to extract (in order of preference)
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

def extract_olmo_evaluations(repo_id="allenai/OLMo-7B"):
    """Extract evaluation scores for OLMo-7B from the model README."""
    
    # Get README content
    api = HfApi()
    readme_content = api.model_info(repo_id, files_metadata=False).card_data
    
    # Download the actual README file
    try:
        readme_path = hf_hub_download(repo_id=repo_id, filename="README.md", repo_type="model")
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_text = f.read()
    except Exception as e:
        print(f"Error downloading README: {e}")
        return None
    
    # Find the main evaluation table comparing different models
    # Look for the table with OLMo 7B results
    lines = readme_text.split('\n')
    
    metrics = []
    in_main_table = False
    header_indices = {}
    
    for i, line in enumerate(lines):
        # Look for the table header with model names
        if '**OLMo 7B**' in line and '|' in line:
            in_main_table = True
            # Parse header to find OLMo 7B column
            headers = [h.strip() for h in line.split('|')]
            for idx, h in enumerate(headers):
                if '**OLMo 7B**' in h:
                    olmo_col_idx = idx
                    break
            continue
        
        # Process table rows when in the main evaluation table
        if in_main_table and '|' in line and not line.strip().startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) > olmo_col_idx:
                # First column is the benchmark name
                benchmark_name = parts[0].strip()
                
                # Check if this is a benchmark we want
                benchmark_key = benchmark_name.lower().replace(' ', '_')
                
                # Handle special cases
                if 'arc_challenge' in benchmark_key or 'arc challenge' in benchmark_name.lower():
                    benchmark_type = 'arc_challenge'
                elif 'arc_easy' in benchmark_key or 'arc easy' in benchmark_name.lower():
                    benchmark_type = 'arc_easy'
                elif 'boolq' in benchmark_key:
                    benchmark_type = 'boolq'
                elif 'copa' in benchmark_key:
                    benchmark_type = 'copa'
                elif 'hellaswag' in benchmark_key:
                    benchmark_type = 'hellaswag'
                elif 'openbookqa' in benchmark_key:
                    benchmark_type = 'openbookqa'
                elif 'piqa' in benchmark_key:
                    benchmark_type = 'piqa'
                elif 'sciq' in benchmark_key:
                    benchmark_type = 'sciq'
                elif 'winogrande' in benchmark_key:
                    benchmark_type = 'winogrande'
                elif 'mmlu' in benchmark_key:
                    benchmark_type = 'mmlu'
                elif 'truthful' in benchmark_key or 'truthfulqa' in benchmark_key:
                    benchmark_type = 'truthfulqa'
                else:
                    # Skip benchmarks not in our target list
                    continue
                
                # Skip average rows
                if 'average' in benchmark_name.lower():
                    continue
                
                # Extract the value from OLMo 7B column
                try:
                    value_str = parts[olmo_col_idx].strip()
                    # Remove any markdown formatting
                    value_str = value_str.replace('*', '').strip()
                    value = float(value_str)
                    
                    # Only add if it's in our target list
                    if benchmark_type in TARGET_BENCHMARKS:
                        metrics.append({
                            'name': benchmark_name,
                            'type': benchmark_type,
                            'value': value
                        })
                except (ValueError, IndexError):
                    continue
        
        # Stop when we hit the next section
        if in_main_table and line.startswith('#'):
            break
    
    # Build the model-index structure
    if metrics:
        model_index = {
            'model-index': [{
                'name': 'OLMo-7B',
                'results': [{
                    'task': {
                        'type': 'text-generation'
                    },
                    'dataset': {
                        'name': 'Language Model Evaluation Benchmarks',
                        'type': 'benchmark'
                    },
                    'metrics': metrics,
                    'source': {
                        'name': 'OLMo-7B Model README',
                        'url': f'https://huggingface.co/{repo_id}'
                    }
                }]
            }]
        }
        return model_index
    
    return None

def main():
    print("Extracting evaluation benchmarks from allenai/OLMo-7B...")
    
    result = extract_olmo_evaluations()
    
    if result:
        # Save to YAML file
        output_file = 'olmo_7b_evaluations.yaml'
        with open(output_file, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"\n✓ Successfully extracted {len(result['model-index'][0]['results'][0]['metrics'])} benchmark scores")
        print(f"✓ Saved to: {output_file}")
        
        # Display the results
        print("\nExtracted benchmarks:")
        for metric in result['model-index'][0]['results'][0]['metrics']:
            print(f"  - {metric['type']}: {metric['value']}")
    else:
        print("✗ Failed to extract evaluations")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
