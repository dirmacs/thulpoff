import yaml
import requests

# Fetch the full README from Hugging Face
readme_url = "https://huggingface.co/allenai/OLMo-7B/raw/main/README.md"
response = requests.get(readme_url)
readme_text = response.text

# Define the benchmarks we want to extract
target_benchmarks = [
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

# Extract scores for OLMo 7B from the comparison table
scores = {}

# Find the comparison table section - look for the specific table with OLMo 7B
lines = readme_text.split('\n')
for i, line in enumerate(lines):
    # Check if this line contains a benchmark name and values
    if '|' not in line:
        continue
        
    parts = [p.strip() for p in line.split('|')]
    if len(parts) < 6:  # Need at least the columns
        continue
    
    # Get the metric name from first column
    metric_name = parts[1].lower().strip() if len(parts) > 1 else ''
    
    # Skip header, separator, and empty rows
    if not metric_name or '-' in metric_name or metric_name == '':
        continue
    
    # Skip aggregate rows (averages)
    if 'average' in metric_name or '**' in metric_name:
        continue
    
    # Get the OLMo value - it should be in the last column (before trailing |)
    olmo_value = parts[-2].strip() if len(parts) >= 2 else ''
    
    # Match to our target benchmarks
    for benchmark in target_benchmarks:
        # Create multiple matching patterns
        patterns = [benchmark, benchmark.replace('_', ''), benchmark.replace('_', ' ')]
        
        # Special handling for specific benchmarks
        if benchmark == 'mmlu' and 'mmlu' in metric_name:
            matched = True
        elif benchmark == 'truthfulqa' and 'truthful' in metric_name:
            matched = True
        elif benchmark == 'arc_challenge' and 'arc_challenge' in metric_name:
            matched = True
        elif benchmark == 'arc_easy' and 'arc_easy' in metric_name:
            matched = True
        elif any(p in metric_name for p in patterns):
            matched = True
        else:
            matched = False
        
        if matched:
            try:
                # Clean the value and convert to float
                value_str = olmo_value.replace('*', '').strip()
                value = float(value_str)
                if benchmark not in scores:  # Only take first occurrence
                    scores[benchmark] = value
                    print(f"Extracted {benchmark}: {value}")
                break
            except (ValueError, AttributeError) as e:
                continue

# Create the model-index YAML structure
model_index = {
    'model-index': [{
        'name': 'OLMo-7B',
        'results': [{
            'task': {
                'type': 'text-generation',
                'name': 'Text Generation'
            },
            'dataset': {
                'name': 'Core Benchmarks',
                'type': 'benchmark'
            },
            'metrics': [],
            'source': {
                'name': 'Model README',
                'url': 'https://huggingface.co/allenai/OLMo-7B'
            }
        }]
    }]
}

# Add metrics in the order specified
metric_names = {
    'arc_challenge': 'ARC Challenge',
    'arc_easy': 'ARC Easy',
    'boolq': 'BoolQ',
    'copa': 'COPA',
    'hellaswag': 'HellaSwag',
    'openbookqa': 'OpenBookQA',
    'piqa': 'PIQA',
    'sciq': 'SciQ',
    'winogrande': 'WinoGrande',
    'mmlu': 'MMLU',
    'truthfulqa': 'TruthfulQA MC2'
}

for key in target_benchmarks:
    if key in scores:
        model_index['model-index'][0]['results'][0]['metrics'].append({
            'type': key,
            'name': metric_names[key],
            'value': scores[key]
        })

# Write to YAML file
output_file = 'olmo_7b_evaluations.yaml'
with open(output_file, 'w') as f:
    yaml.dump(model_index, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f"\n✓ Successfully wrote {len(scores)} benchmarks to {output_file}")
print(f"\nBenchmarks included: {', '.join(sorted(scores.keys()))}")
print(f"\nMissing benchmarks: {', '.join([b for b in target_benchmarks if b not in scores])}")
