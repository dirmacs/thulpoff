import yaml, sys

if len(sys.argv) != 3:
    print('Usage: filter_yaml.py <input_yaml> <output_yaml>')
    sys.exit(1)

input_path, output_path = sys.argv[1:3]

with open(input_path, 'r') as f:
    lines = f.readlines()

# Clean header lines and leading blanks
cleaned = []
for line in lines:
    if not cleaned and line.strip() == '':
        continue
    if line.lstrip().startswith('Extracted evaluations'):
        continue
    cleaned.append(line)
content = ''.join(cleaned)

data = yaml.safe_load(content)

# Allowed benchmark identifiers (as they appear in 'type' field, normalized)
allowed = {
    'arc_challenge', 'arc_easy', 'boolq', 'copa', 'hellaswag',
    'openbookqa', 'piqa', 'sciq', 'winogrande', 'mmlu', 'truthfulqa'
}

model_index = data.get('model-index', [])
if not model_index:
    sys.exit('No model-index found')
model_entry = model_index[0]
results = model_entry.get('results', [])
if not results:
    sys.exit('No results found')
result_entry = results[0]
metrics = result_entry.get('metrics', [])

filtered = []
for m in metrics:
    typ = m.get('type', '').lower()
    # Normalize: remove parentheses and spaces, keep underscores
    norm = typ.replace('(', '').replace(')', '').replace(' ', '')
    # Map variations for mmlu and truthfulqa
    if norm.startswith('mmlu'):
        key = 'mmlu'
    elif norm.startswith('truthfulqa'):
        key = 'truthfulqa'
    else:
        key = norm
    if key in allowed:
        filtered.append(m)

result_entry['metrics'] = filtered

with open(output_path, 'w') as f:
    yaml.dump(data, f, sort_keys=False)
