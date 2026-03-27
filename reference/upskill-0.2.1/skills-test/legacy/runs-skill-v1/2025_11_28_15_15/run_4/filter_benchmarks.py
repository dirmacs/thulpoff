import yaml
import sys

# Get the full extraction output
full_output = sys.stdin.read()

# Parse the YAML
data = yaml.safe_load(full_output)

# Filter metrics to only include the specified benchmarks
allowed_benchmarks = {
    'arc_challenge', 'arc_easy', 'boolq', 'copa', 'hellaswag', 
    'openbookqa', 'piqa', 'sciq', 'winogrande', 'mmlu', 'truthfulqa',
    'mmlu_(5_shot_mc)', 'truthfulqa_(mc2)'
}

if data and 'model-index' in data:
    for model_entry in data['model-index']:
        if 'results' in model_entry:
            for result in model_entry['results']:
                if 'metrics' in result:
                    filtered_metrics = []
                    for metric in result['metrics']:
                        metric_name = metric.get('type', '').lower()
                        if metric_name in allowed_benchmarks:
                            # Clean up the benchmark names for consistency
                            if 'arc_challenge' in metric_name:
                                metric['type'] = 'arc_challenge'
                            elif 'arc_easy' in metric_name:
                                metric['type'] = 'arc_easy'
                            elif 'mmlu' in metric_name and '5_shot_mc' in metric_name:
                                metric['type'] = 'mmlu'
                            elif 'truthfulqa' in metric_name and 'mc2' in metric_name:
                                metric['type'] = 'truthfulqa'
                            
                            # Clean metric names to remove reference models
                            metric_name_clean = metric.get('name', '')
                            # Remove reference to other models in parentheses
                            if '(' in metric_name_clean and ')' in metric_name_clean:
                                if 'OLMo' in metric_name_clean:
                                    # Keep OLMo specific mentions
                                    pass
                                elif metric_name_clean.startswith('**') or 'random' in metric_name_clean:
                                    # Skip average and random baselines
                                    continue
                                else:
                                    # Remove model reference from name
                                    metric_name_clean = metric_name_clean.split('(')[0].strip()
                            
                            metric['name'] = metric_name_clean
                            filtered_metrics.append(metric)
                    
                    result['metrics'] = filtered_metrics

# Output the filtered YAML
yaml.dump(data, sys.stdout, default_flow_style=False, sort_keys=False)
