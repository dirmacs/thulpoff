#!/usr/bin/env python3
"""Extract specific evaluation benchmarks for OLMo-7B and save to YAML."""

import yaml
import re
from huggingface_hub import hf_hub_download, hf_api

# Target benchmarks to extract
TARGET_BENCHMARKS = [
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

def extract_olmo_evaluations(repo_id: str):
    """Extract OLMo 7B evaluation scores from README."""
    
    # Get README content
    api = hf_api.HfApi()
    model_info = api.model_info(repo_id, files_metadata=False)
    
    # Download README
    try:
        readme_path = hf_hub_download(
            repo_id=repo_id,
            filename="README.md",
            repo_type="model"
        )
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        print(f"Error downloading README: {e}")
        return None
    
    # Parse the main evaluation table
    # Looking for the table with OLMo 7B column
    evaluations = {}
    
    # Find the main comparison table
    # Pattern: | benchmark_name | ... | **OLMo 7B** (ours) |
    lines = readme_content.split('\n')
    
    in_main_table = False
    olmo_col_idx = None
    
    for i, line in enumerate(lines):
        # Detect table header with OLMo 7B
        if '**OLMo 7B**' in line and '|' in line:
            in_main_table = True
            # Find which column has OLMo 7B
            cols = [c.strip() for c in line.split('|')]
            for idx, col in enumerate(cols):
                if '**OLMo 7B**' in col:
                    olmo_col_idx = idx
                    break
            continue
        
        # Skip separator line
        if in_main_table and '---' in line:
            continue
            
        # Parse data rows
        if in_main_table and '|' in line and olmo_col_idx is not None:
            cols = [c.strip() for c in line.split('|')]
            
            # Check if we've left the table (empty row or section header)
            if len(cols) < olmo_col_idx + 1:
                in_main_table = False
                continue
                
            # Get benchmark name and OLMo score
            benchmark_name = cols[1].strip() if len(cols) > 1 else ""
            olmo_score = cols[olmo_col_idx].strip() if len(cols) > olmo_col_idx else ""
            
            # Stop at empty benchmark name or summary rows
            if not benchmark_name or '**' in benchmark_name:
                in_main_table = False
                continue
            
            # Clean benchmark name
            benchmark_clean = benchmark_name.lower().replace(' ', '_')
            
            # Check if this is a target benchmark
            for target in TARGET_BENCHMARKS:
                if target in benchmark_clean:
                    try:
                        score = float(olmo_score)
                        evaluations[benchmark_name] = score
                    except ValueError:
                        pass
    
    # Also check for MMLU and TruthfulQA which might be listed separately
    # Look for "MMLU (5 shot MC)" and "truthfulQA (MC2)"
    for line in lines:
        if '|' not in line:
            continue
        
        cols = [c.strip() for c in line.split('|')]
        if len(cols) < 2:
            continue
            
        benchmark_name = cols[1] if len(cols) > 1 else ""
        
        # Check for MMLU
        if 'MMLU' in benchmark_name and 'mmlu' not in [k.lower() for k in evaluations.keys()]:
            if olmo_col_idx and len(cols) > olmo_col_idx:
                try:
                    score = float(cols[olmo_col_idx].strip())
                    evaluations[benchmark_name] = score
                except (ValueError, IndexError):
                    pass
        
        # Check for TruthfulQA
        if 'truthful' in benchmark_name.lower() and 'truthful' not in [k.lower() for k in evaluations.keys()]:
            if olmo_col_idx and len(cols) > olmo_col_idx:
                try:
                    score = float(cols[olmo_col_idx].strip())
                    evaluations[benchmark_name] = score
                except (ValueError, IndexError):
                    pass
    
    return evaluations

def create_model_index_yaml(repo_id: str, evaluations: dict):
    """Create model-index YAML format."""
    
    metrics = []
    for benchmark_name, score in evaluations.items():
        # Clean benchmark name for type
        benchmark_type = benchmark_name.lower()
        # Remove parenthetical notes
        benchmark_type = re.sub(r'\s*\([^)]*\)', '', benchmark_type)
        benchmark_type = benchmark_type.strip().replace(' ', '_')
        
        metrics.append({
            'name': benchmark_name,
            'type': benchmark_type,
            'value': score
        })
    
    # Sort by benchmark type for consistency
    metrics.sort(key=lambda x: x['type'])
    
    model_index = {
        'model-index': [{
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
                    'name': 'Model README',
                    'url': f'https://huggingface.co/{repo_id}'
                }
            }]
        }]
    }
    
    return model_index

def main():
    repo_id = "allenai/OLMo-7B"
    
    print(f"Extracting evaluations from {repo_id}...")
    evaluations = extract_olmo_evaluations(repo_id)
    
    if not evaluations:
        print("No evaluations found!")
        return
    
    print(f"\nFound {len(evaluations)} evaluation scores:")
    for name, score in evaluations.items():
        print(f"  - {name}: {score}")
    
    # Create model-index YAML
    model_index = create_model_index_yaml(repo_id, evaluations)
    
    # Save to file
    output_file = "olmo_7b_evaluations.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(model_index, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✓ Saved to {output_file}")
    
    # Display the YAML content
    print(f"\nGenerated YAML content:")
    print("=" * 60)
    with open(output_file, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    main()
