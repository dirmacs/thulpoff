import yaml
import subprocess
import json

# Define the benchmarks we want to keep
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
    'mmlu_(5_shot_mc)',  # This is the MMLU from OLMo-7B
    'truthfulqa_(mc2)',   # This is the TruthfulQA from OLMo-7B
}

# Run the extraction
result = subprocess.run([
    'python', '../skills/hf_model_evaluation/scripts/evaluation_manager.py',
    'extract-readme',
    '--repo-id', 'allenai/OLMo-7B',
    '--dry-run'
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error extracting evaluations: {result.stderr}")
    exit(1)

# Parse the YAML output
output = result.stdout
yaml_start = output.find('model-index:')
yaml_content = output[yaml_start:]

try:
    data = yaml.safe_load(yaml_content)
except Exception as e:
    print(f"Error parsing YAML: {e}")
    exit(1)

# Filter metrics
if data and 'model-index' in data:
    model_data = data['model-index'][0]
    results = model_data['results'][0]
    
    # Filter metrics to only include allowed benchmarks
    filtered_metrics = []
    for metric in results['metrics']:
        metric_type = metric.get('type', '').lower()
        # Check if this metric type is in our allowed list
        if any(allowed.lower() in metric_type.lower() for allowed in ALLOWED_BENCHMARKS):
            filtered_metrics.append(metric)
    
    # Update the results with filtered metrics
    results['metrics'] = filtered_metrics
    
    # Create output structure
    output_data = {
        'model-index': [model_data]
    }
    
    # Save to YAML file
    with open('olmo_7b_evaluations.yaml', 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Successfully extracted and filtered {len(filtered_metrics)} benchmark metrics")
    print(f"✓ Saved to olmo_7b_evaluations.yaml")
    print(f"\nIncluded benchmarks:")
    for metric in filtered_metrics:
        print(f"  - {metric['name']}: {metric['value']}")
else:
    print("Error: Could not find model-index in extraction output")
    exit(1)
