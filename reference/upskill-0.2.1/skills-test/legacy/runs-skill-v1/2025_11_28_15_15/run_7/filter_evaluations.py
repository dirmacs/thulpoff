#!/usr/bin/env python3

import yaml
import sys

# List of benchmarks we want to keep
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

# Read the raw YAML from stdin
raw_yaml = sys.stdin.read()

# Parse it
data = yaml.safe_load(raw_yaml)

# Filter out only the benchmarks we want
if 'model-index' in data and len(data['model-index']) > 0:
    model_data = data['model-index'][0]
    
    # Filter metrics to only include allowed benchmarks
    filtered_metrics = []
    for result in model_data['results']:
        filtered_result_metrics = []
        for metric in result['metrics']:
            # Check if the benchmark name is in our allowed list
            benchmark_name = metric['name'].lower()
            
            # Clean up the benchmark name to match our filter
            # Remove anything in parentheses and extra formatting
            if '(' in benchmark_name:
                benchmark_name = benchmark_name.split('(')[0].strip()
            
            # Remove markdown formatting
            benchmark_name = benchmark_name.replace('**', '').replace('*', '').strip()
            
            if benchmark_name in ALLOWED_BENCHMARKS:
                # Update the metric type to be clean
                metric['type'] = benchmark_name
                filtered_result_metrics.append(metric)
        
        # Only keep results that have metrics after filtering
        if filtered_result_metrics:
            result['metrics'] = filtered_result_metrics
            filtered_metrics.append(result)
    
    # Keep only results with metrics
    model_data['results'] = filtered_metrics
    
    # Update the model-index
    data['model-index'] = [model_data]

# Output the filtered YAML
yaml.dump(data, sys.stdout, default_flow_style=False, sort_keys=False)
