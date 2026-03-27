#!/usr/bin/env python3
"""Extract and filter OLMo-7B evaluation scores."""

import yaml
import re
from pathlib import Path
from huggingface_hub import hf_hub_download

# Benchmarks to include
ALLOWED_BENCHMARKS = {
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

def normalize_benchmark_name(name):
    """Normalize benchmark name for matching."""
    # Remove extra text in parentheses
    name = re.sub(r'\s*\([^)]*\)', '', name).strip()
    # Convert to lowercase and remove special chars
    name = name.lower().replace(' ', '_').replace('-', '_')
    # Handle specific cases
    name = name.replace('truthfulqa_mc2', 'truthfulqa')
    name = name.replace('mmlu_5_shot_mc', 'mmlu')
    return name

def extract_olmo_benchmarks():
    """Extract OLMo-7B evaluation scores from model README."""
    
    print("📥 Fetching model README...")
    readme_path = hf_hub_download(
        repo_id="allenai/OLMo-7B",
        filename="README.md",
        repo_type="model"
    )
    
    with open(readme_path, 'r') as f:
        readme = f.read()
    
    print("🔍 Parsing evaluation table...")
    
    # Find the table that contains the benchmark comparisons
    lines = readme.split('\n')
    
    table_start_idx = None
    for i, line in enumerate(lines):
        if '**OLMo 7B**' in line and '(ours)' in line and '|' in line:
            # This is the header line
            table_start_idx = i
            break
    
    if table_start_idx is None:
        print("❌ Could not find evaluation table")
        return None
    
    print(f"✓ Found table at line {table_start_idx}")
    
    # Parse the header to find column indices
    header_line = lines[table_start_idx]
    headers = [h.strip() for h in header_line.split('|')]
    headers = [h for h in headers if h]  # Remove empty
    
    print(f"Headers ({len(headers)} columns): {headers}")
    
    # Find OLMo 7B column - should be the LAST column (index 5 = position 6)
    olmo_idx = None
    for i, h in enumerate(headers):
        if 'OLMo 7B' in h and 'ours' in h:
            olmo_idx = i
            break
    
    if olmo_idx is None:
        print("❌ Could not find OLMo 7B column")
        return None
    
    print(f"✓ Found OLMo 7B at column index {olmo_idx} (header: '{headers[olmo_idx]}')")
    
    # Parse data rows
    metrics = []
    for line in lines[table_start_idx + 2:]:  # Skip header and separator
        if not line.strip() or not '|' in line:
            # End of table
            if metrics:  # Only break if we've found some metrics
                break
            continue
        
        if line.startswith('|--'):  # Skip separator lines
            continue
        
        cols = [c.strip() for c in line.split('|')]
        cols = [c for c in cols if c]  # Remove empty
        
        if len(cols) <= olmo_idx:
            print(f"  Skipping line (not enough columns): {line[:50]}")
            continue
        
        benchmark_name = cols[0].strip()
        
        # Get the actual OLMo value from the LAST column
        value_str = cols[-1].strip()  # Use last column instead of olmo_idx
        
        print(f"  Checking: {benchmark_name} = {value_str} (from column {len(cols)-1})")
        
        # Skip empty or non-numeric values
        if not value_str or value_str == '-':
            continue
        
        try:
            value = float(value_str)
        except ValueError:
            print(f"    Skipping (not numeric): {value_str}")
            continue
        
        # Normalize and check if allowed
        normalized_name = normalize_benchmark_name(benchmark_name)
        
        # Check if this is an allowed benchmark
        is_allowed = False
        metric_type = None
        for allowed in ALLOWED_BENCHMARKS:
            if allowed in normalized_name:
                is_allowed = True
                metric_type = allowed
                break
        
        if not is_allowed:
            print(f"    Skipping (not in allowed list): {benchmark_name} (normalized: {normalized_name})")
            continue
        
        # Create clean metric name
        clean_name = benchmark_name.split('(')[0].strip()
        
        print(f"    ✓ ADDED: {clean_name}: {value}")
        
        metrics.append({
            'name': clean_name,
            'type': metric_type,
            'value': value
        })
    
    print(f"\n✓ Extracted {len(metrics)} benchmark scores")
    
    if not metrics:
        print("❌ No metrics extracted")
        return None
    
    # Create model-index structure
    model_index = {
        'model-index': [{
            'name': 'OLMo-7B',
            'results': [{
                'task': {
                    'type': 'text-generation'
                },
                'dataset': {
                    'name': 'Evaluation Benchmarks',
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

if __name__ == '__main__':
    print("=" * 60)
    print("OLMo-7B Evaluation Extraction")
    print("=" * 60)
    
    result = extract_olmo_benchmarks()
    
    if result:
        output_file = Path('olmo_7b_evaluations.yaml')
        
        # Write YAML with proper formatting
        with open(output_file, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"\n✅ Successfully saved to {output_file}")
        print(f"\n📊 Summary:")
        metrics = result['model-index'][0]['results'][0]['metrics']
        for m in metrics:
            print(f"  - {m['name']}: {m['value']}")
        
        print(f"\n💾 File location: {output_file.absolute()}")
    else:
        print("\n❌ Failed to extract evaluations")
        exit(1)
