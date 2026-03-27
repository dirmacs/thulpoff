import yaml
import sys

# Read the current YAML file
with open('olmo_7b_evaluations.yaml', 'r') as f:
    content = f.read()

# Parse the YAML lines but skip the first line (Preview message)
yaml_lines = content.split('\n')[1:]  # Skip the first line
yaml_data = '\n'.join(yaml_lines)

data = yaml.safe_load(yaml_data)

# Write clean YAML back
with open('olmo_7b_evaluations.yaml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print("Cleaned YAML file created successfully!")
