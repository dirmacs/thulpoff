import yaml
import re
from huggingface_hub import hf_hub_download, list_repo_refs
from huggingface_hub import HfApi

# Get the README content
api = HfApi()
readme_content = api.model_info("allenai/OLMo-7B", files_metadata=False).card_data

# Download and read the README file
try:
    from huggingface_hub import hf_hub_url
    import requests
    readme_url = "https://huggingface.co/allenai/OLMo-7B/raw/main/README.md"
    response = requests.get(readme_url)
    readme_text = response.text
except:
    # Fallback: use the truncated version we have
    readme_text = """
| | [Llama 7B](https://arxiv.org/abs/2302.13971) | [Llama 2 7B](https://huggingface.co/meta-llama/Llama-2-7b) | [Falcon 7B](https://huggingface.co/tiiuae/falcon-7b) | [MPT 7B](https://huggingface.co/mosaicml/mpt-7b) | **OLMo 7B** (ours) |
| --------------------------------- | -------- | ---------- | --------- | ------ | ------- |
| arc_challenge       | 44.5             | 39.8             | 47.5         | 46.5         | 48.5            |
| arc_easy            | 57.0             | 57.7             | 70.4         | 70.5         | 65.4            |
| boolq               | 73.1             | 73.5             | 74.6         | 74.2         | 73.4            |
| copa                | 85.0             | 87.0             | 86.0         | 85.0         | 90              |
| hellaswag           | 74.5             | 74.5             | 75.9         | 77.6         | 76.4            |
| openbookqa          | 49.8             | 48.4             | 53.0         | 48.6         | 50.2            |
| piqa                | 76.3             | 76.4             | 78.5         | 77.3         | 78.4            |
| sciq                | 89.5             | 90.8             | 93.9         | 93.7         | 93.8            |
| winogrande          | 68.2             | 67.3             | 68.9         | 69.9         | 67.9            |
| **Core tasks average**  | 68.7             | 68.4             | 72.1         | 71.5         | 71.6            |
| truthfulQA (MC2)    | 33.9             | 38.5             | 34.0         | 33           | 36.0            |
| MMLU (5 shot MC)    | 31.5             | 45.0             | 24.0         | 30.8         | 28.3            |
"""

# Define the benchmarks we want to extract
target_benchmarks = {
    'arc_challenge': 'arc_challenge',
    'arc_easy': 'arc_easy', 
    'boolq': 'boolq',
    'copa': 'copa',
    'hellaswag': 'hellaswag',
    'openbookqa': 'openbookqa',
    'piqa': 'piqa',
    'sciq': 'sciq',
    'winogrande': 'winogrande',
    'mmlu': 'MMLU (5 shot MC)',
    'truthfulqa': 'truthfulQA (MC2)'
}

# Extract scores for OLMo 7B from the table
scores = {}

# Parse the comparison table - OLMo 7B is in the last column
lines = readme_text.split('\n')
for line in lines:
    if '|' in line and any(bench in line.lower() for bench in target_benchmarks.keys()):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 6:  # Should have at least 6 columns (empty, Llama, Llama2, Falcon, MPT, OLMo, empty)
            metric_name = parts[1].lower().strip()
            olmo_value = parts[-2].strip()  # Second to last (before empty trailing element)
            
            # Match the benchmark
            for key, pattern in target_benchmarks.items():
                if pattern.lower() in metric_name or key in metric_name:
                    try:
                        # Clean the value and convert to float
                        value_str = olmo_value.replace('*', '').strip()
                        value = float(value_str)
                        scores[key] = value
                        print(f"Extracted {key}: {value}")
                    except ValueError:
                        print(f"Warning: Could not parse value '{olmo_value}' for {key}")

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

for key in ['arc_challenge', 'arc_easy', 'boolq', 'copa', 'hellaswag', 
            'openbookqa', 'piqa', 'sciq', 'winogrande', 'mmlu', 'truthfulqa']:
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
