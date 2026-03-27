import yaml

# Define the benchmarks we want to keep (actual model scores only)
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
    'truthfulqa',
}

# Read the current YAML file
with open('olmo_7b_evaluations.yaml', 'r') as f:
    data = yaml.safe_load(f)

# Filter metrics
if data and 'model-index' in data:
    model_data = data['model-index'][0]
    results = model_data['results'][0]
    
    # Filter metrics to only include allowed benchmarks and exclude random baselines
    filtered_metrics = []
    for metric in results['metrics']:
        metric_type = metric.get('type', '').lower()
        metric_name = metric.get('name', '').lower()
        
        # Skip random baseline scores
        if 'random' in metric_name:
            continue
        
        # Check if this metric type is in our allowed list
        if any(allowed.lower() in metric_type.lower() for allowed in ALLOWED_BENCHMARKS):
            filtered_metrics.append(metric)
    
    # Update the results with filtered metrics
    results['metrics'] = filtered_metrics
    
    # Create output structure
    output_data = {
        'model-index': [model_data]
    }
    
    # Save to YAML file with proper formatting
    with open('olmo_7b_evaluations.yaml', 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"✓ Successfully filtered and cleaned evaluation data")
    print(f"✓ Extracted {len(filtered_metrics)} benchmark metrics (excluding random baselines)")
    print(f"✓ Saved to olmo_7b_evaluations.yaml")
    print(f"\nIncluded benchmarks (model scores only):")
    for metric in filtered_metrics:
        print(f"  - {metric['name']}: {metric['value']}")
else:
    print("Error: Could not find model-index in YAML")
    exit(1)
