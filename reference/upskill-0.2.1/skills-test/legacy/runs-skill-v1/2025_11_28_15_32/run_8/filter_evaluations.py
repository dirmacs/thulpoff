#!/usr/bin/env python3
"""Filter evaluation results to specific benchmarks."""

import yaml
from huggingface_hub import hf_hub_download, HfApi
import re

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

def normalize_metric_type(metric_type):
    """Normalize metric type for matching."""
    # Remove markdown, links, parentheses, special chars
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', metric_type)  # Remove links
    cleaned = re.sub(r'\*\*', '', cleaned)  # Remove bold
    cleaned = re.sub(r'[_\(\)\s\-]+', '_', cleaned.lower())  # Normalize
    cleaned = cleaned.strip('_')
    return cleaned

def matches_allowed_benchmark(metric_type):
    """Check if metric type matches any allowed benchmark."""
    normalized = normalize_metric_type(metric_type)
    
    for allowed in ALLOWED_BENCHMARKS:
        # Check if the allowed benchmark appears in the normalized type
        if allowed in normalized or normalized.startswith(allowed):
            return True
    return False

def extract_evaluations(repo_id):
    """Extract and filter evaluation results from model README."""
    api = HfApi()
    
    # Get README content
    try:
        readme_path = hf_hub_download(repo_id=repo_id, filename="README.md", repo_type="model")
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        print(f"Error fetching README: {e}")
        return None
    
    # Parse model card metadata
    try:
        card = api.model_card_data(repo_id)
        if hasattr(card, 'data') and card.data:
            model_index = card.data.get('model-index', [])
        else:
            model_index = []
    except:
        model_index = []
    
    # If no model-index in metadata, try to find benchmarks in tables
    if not model_index:
        # Find tables in README
        tables = re.findall(r'\|[^\n]+\|[\s\S]*?\n\s*\n', readme_content)
        
        if tables:
            # Look for Llama 7B benchmark table (the comparison table)
            for table in tables:
                if 'Llama 7B' in table and any(bench in table.lower() for bench in ALLOWED_BENCHMARKS):
                    # Parse the table
                    metrics = []
                    lines = [l.strip() for l in table.split('\n') if '|' in l]
                    
                    for line in lines[2:]:  # Skip header and separator
                        cells = [c.strip() for c in line.split('|')[1:-1]]
                        if len(cells) >= 2:
                            benchmark = cells[0].strip()
                            
                            # Try to find OLMo 7B value
                            # Table format: benchmark | OLMo 1B | OLMo 7B | OLMo 7B-Twin | Llama 7B | ...
                            if len(cells) >= 3:  # Need at least benchmark + 2 models
                                # OLMo 7B is typically in column 2 (index 1 after benchmark)
                                try:
                                    value = float(cells[2].strip())
                                    
                                    # Normalize benchmark name
                                    normalized_bench = normalize_metric_type(benchmark)
                                    
                                    if matches_allowed_benchmark(benchmark):
                                        metrics.append({
                                            'name': benchmark,
                                            'type': normalized_bench,
                                            'value': value
                                        })
                                except (ValueError, IndexError):
                                    continue
                    
                    if metrics:
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
                                    'name': 'Model README',
                                    'url': f'https://huggingface.co/{repo_id}'
                                }
                            }]
                        }]
    
    # Filter existing model-index
    if model_index:
        filtered_index = []
        for model in model_index:
            filtered_results = []
            for result in model.get('results', []):
                filtered_metrics = []
                for metric in result.get('metrics', []):
                    metric_type = metric.get('type', '')
                    if matches_allowed_benchmark(metric_type):
                        filtered_metrics.append(metric)
                
                if filtered_metrics:
                    filtered_result = result.copy()
                    filtered_result['metrics'] = filtered_metrics
                    filtered_results.append(filtered_result)
            
            if filtered_results:
                filtered_model = model.copy()
                filtered_model['results'] = filtered_results
                filtered_index.append(filtered_model)
        
        return {'model-index': filtered_index}
    
    return None

def main():
    repo_id = "allenai/OLMo-7B"
    
    print(f"Extracting evaluations from {repo_id}...")
    result = extract_evaluations(repo_id)
    
    if result:
        # Save to YAML
        output_file = "olmo_7b_evaluations.yaml"
        with open(output_file, 'w') as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"\n✓ Saved filtered evaluations to {output_file}")
        print(f"\nContents:")
        print(yaml.dump(result, default_flow_style=False, sort_keys=False, allow_unicode=True))
    else:
        print("No evaluation results found.")

if __name__ == "__main__":
    main()
