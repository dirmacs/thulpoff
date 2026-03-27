#!/usr/bin/env python3
"""
Extract specific evaluation benchmarks from allenai/OLMo-7B model card.
"""

import yaml
from huggingface_hub import hf_hub_download

# Benchmarks to extract (exact names as they appear in the table)
TARGET_BENCHMARKS = {
    "arc_challenge": "arc_challenge",
    "arc_easy": "arc_easy",
    "boolq": "boolq",
    "copa": "copa",
    "hellaswag": "hellaswag",
    "openbookqa": "openbookqa",
    "piqa": "piqa",
    "sciq": "sciq",
    "winogrande": "winogrande",
    "mmlu": "mmlu",
    "truthfulqa": "truthfulqa"
}

def extract_olmo_evaluations(repo_id="allenai/OLMo-7B"):
    """Extract evaluation scores for OLMo-7B from the model README."""
    
    # Download the actual README file
    try:
        readme_path = hf_hub_download(repo_id=repo_id, filename="README.md", repo_type="model")
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_text = f.read()
    except Exception as e:
        print(f"Error downloading README: {e}")
        return None
    
    # Find the main evaluation table comparing different models
    lines = readme_text.split('\n')
    
    metrics = []
    in_main_table = False
    
    for i, line in enumerate(lines):
        # Look for the table header with OLMo 7B column
        if '**OLMo 7B**' in line and 'Llama 7B' in line and '|' in line:
            in_main_table = True
            print(f"Found evaluation table at line {i}")
            continue
        
        # Skip the separator line
        if in_main_table and '---' in line:
            continue
        
        # Process table rows when in the main evaluation table
        if in_main_table and '|' in line:
            parts = [p.strip() for p in line.split('|')]
            
            # Need at least 7 parts (empty, benchmark, 5 models, empty)
            if len(parts) < 7:
                continue
            
            # Benchmark name is in column 1
            benchmark_name = parts[1].strip()
            
            # Skip empty rows
            if not benchmark_name or not parts[6]:
                continue
            
            benchmark_key = benchmark_name.lower()
            
            # Check if this is a benchmark we want (excluding averages and GSM8k)
            if 'average' in benchmark_key or 'gsm8k' in benchmark_key:
                continue
            
            # Try to match against our target benchmarks
            matched_type = None
            for key, benchmark_type in TARGET_BENCHMARKS.items():
                if key in benchmark_key:
                    matched_type = benchmark_type
                    break
            
            if not matched_type:
                continue
            
            # Extract the value from OLMo 7B column (index 6)
            try:
                value_str = parts[6].strip()
                # Remove any markdown formatting
                value_str = value_str.replace('*', '').strip()
                # Handle special cases like "8.5 (8shot CoT)"
                if '(' in value_str:
                    value_str = value_str.split('(')[0].strip()
                value = float(value_str)
                
                metrics.append({
                    'name': benchmark_name,
                    'type': matched_type,
                    'value': value
                })
                print(f"  ✓ Extracted: {matched_type:15} = {value:6.1f}  ({benchmark_name})")
            except (ValueError, IndexError) as e:
                print(f"  ✗ Warning: Could not parse value for {benchmark_name}: {e}")
                continue
        
        # Stop when we hit the next section (1B model table)
        if in_main_table and '1B model' in line:
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
    print("=" * 60)
    print("Extracting evaluation benchmarks from allenai/OLMo-7B")
    print("=" * 60)
    print()
    
    result = extract_olmo_evaluations()
    
    if result:
        # Save to YAML file
        output_file = 'olmo_7b_evaluations.yaml'
        with open(output_file, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print()
        print("=" * 60)
        print(f"✓ Successfully extracted {len(result['model-index'][0]['results'][0]['metrics'])} benchmark scores")
        print(f"✓ Saved to: {output_file}")
        print("=" * 60)
        
        # Display summary
        print("\nBenchmarks included:")
        for metric in result['model-index'][0]['results'][0]['metrics']:
            print(f"  • {metric['type']:15} : {metric['value']:6.1f}")
        
        print(f"\nSource: {result['model-index'][0]['results'][0]['source']['url']}")
    else:
        print("✗ Failed to extract evaluations")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
