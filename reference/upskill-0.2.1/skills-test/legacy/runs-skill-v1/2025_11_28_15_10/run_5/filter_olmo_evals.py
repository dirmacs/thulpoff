#!/usr/bin/env python3

import yaml
import re
import subprocess

# Required benchmarks to keep
REQUIRED_BENCHMARKS = [
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

def extract_evaluations():
    """Extract evaluations from the model README"""
    result = subprocess.run([
        'python', '../skills/hf_model_evaluation/scripts/evaluation_manager.py', 
        'extract-readme',
        '--repo-id', 'allenai/OLMo-7B',
        '--model-name-override', '**OLMo 7B** (ours)',
        '--dry-run'
    ], capture_output=True, text=True)
    
    # Extract the YAML content from the output
    lines = result.stdout.split('\n')
    yaml_start = None
    yaml_end = None
    
    for i, line in enumerate(lines):
        if line.strip() == 'model-index:':
            yaml_start = i
        elif yaml_start is not None and line.strip() == 'source:':
            # Find the end of the metrics section
            for j in range(i, len(lines)):
                if lines[j].strip().startswith('name:') and 'Model README' in lines[j]:
                    yaml_end = j
                    break
            break
    
    if yaml_start is None or yaml_end is None:
        raise ValueError("Could not find YAML content in extraction output")
    
    yaml_content = '\n'.join(lines[yaml_start:yaml_end])
    return yaml_content

def filter_benchmarks(yaml_content):
    """Filter to only include required benchmarks"""
    data = yaml.safe_load(yaml_content)
    
    if not data or 'model-index' not in data:
        raise ValueError("Invalid YAML structure")
    
    # Process the first (and only) model entry
    model_data = data['model-index'][0]
    
    # Filter metrics to only include required benchmarks
    filtered_metrics = []
    
    for metric in model_data['results'][0]['metrics']:
        metric_name = metric['type']
        
        # Clean up the metric name by removing special characters and normalizing
        clean_name = re.sub(r'[^\w]', '', metric_name.lower())
        
        # Check if this is one of our required benchmarks
        is_required = False
        for required in REQUIRED_BENCHMARKS:
            if required.lower() in clean_name:
                is_required = True
                break
        
        if is_required:
            # Clean up the metric name for the final output
            metric['type'] = metric_name.split('(')[0].strip().lower()
            filtered_metrics.append(metric)
    
    # Update the model data with filtered metrics
    model_data['results'][0]['metrics'] = filtered_metrics
    
    # Create the final structure
    output_data = {
        'model-index': [model_data]
    }
    
    return output_data

def main():
    """Main function to extract and filter evaluations"""
    try:
        # Extract evaluations from README
        print("Extracting evaluations from model README...")
        yaml_content = extract_evaluations()
        
        # Filter to required benchmarks
        print("Filtering to required benchmarks...")
        filtered_data = filter_benchmarks(yaml_content)
        
        # Add source attribution
        filtered_data['model-index'][0]['results'][0]['source'] = {
            'name': 'Model README',
            'url': 'https://huggingface.co/allenai/OLMo-7B'
        }
        
        # Save to YAML file
        output_file = 'olmo_7b_evaluations.yaml'
        with open(output_file, 'w') as f:
            yaml.dump(filtered_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"Successfully saved filtered evaluations to {output_file}")
        
        # Display the saved content
        print("\nSaved YAML content:")
        with open(output_file, 'r') as f:
            print(f.read())
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
