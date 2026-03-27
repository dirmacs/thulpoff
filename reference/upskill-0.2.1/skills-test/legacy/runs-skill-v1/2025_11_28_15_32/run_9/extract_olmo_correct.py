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

# Find the comparison table section
lines = readme_text.split('\n')
in_table = False
for i, line in enumerate(lines):
    # Look for the header row with model names
    if '**OLMo 7B**' in line and 'Llama 7B' in line:
        in_table = True
        continue
    
    if in_table and '|' in line:
        # Skip separator lines
        if '---' in line:
            continue
            
        # Exit table when we hit a line without proper structure
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            in_table = False
            continue
            
        # Extract metric name and OLMo value (last actual column)
        metric_name = parts[1].lower().strip()
        olmo_value = parts[-2].strip()  # Second to last (before empty trailing)
        
        # Skip empty or non-data rows
        if not metric_name or metric_name.startswith('-'):
            continue
            
        # Skip aggregate rows
        if 'average' in metric_name or 'core tasks' in metric_name or 'full' in metric_name:
            continue
        
        # Match to our target benchmarks
        matched = False
        for benchmark in target_benchmarks:
            if benchmark == 'mmlu' and 'mmlu' in metric_name:
                matched = True
                key = 'mmlu'
                break
            elif benchmark == 'truthfulqa' and 'truthful' in metric_name:
                matched = True
                key = 'truthfulqa'
                break
            elif benchmark in metric_name.replace('_', '').replace(' ', ''):
                matched = True
                key = benchmark
                break
        
        if matched:
            try:
                # Clean the value and convert to float
                value_str = olmo_value.replace('*', '').strip()
                value = float(value_str)
                if key not in scores:  # Only take first occurrence
                    scores[key] = value
                    print(f"Extracted {key}: {value}")
            except ValueError:
                print(f"Warning: Could not parse value '{olmo_value}' for {metric_name}")

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
print(f"\nBenchmarks included: {', '.join(scores.keys())}")
print(f"\nValidation: All scores are for OLMo 7B only, excluding averages and baselines.")
