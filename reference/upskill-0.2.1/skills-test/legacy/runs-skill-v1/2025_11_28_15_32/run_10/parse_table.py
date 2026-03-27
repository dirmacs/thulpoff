#!/usr/bin/env python3
import re
from huggingface_hub import hf_hub_download

# Download README
readme_path = hf_hub_download(repo_id="allenai/OLMo-7B", filename="README.md", repo_type="model")
with open(readme_path, 'r', encoding='utf-8') as f:
    readme_text = f.read()

# Find the evaluation table section
lines = readme_text.split('\n')

# Look for the table with OLMo results
for i, line in enumerate(lines):
    if 'arc_challenge' in line and '|' in line:
        # Print context around this line
        print("Found evaluation table around line", i)
        print("\n".join(lines[max(0, i-5):min(len(lines), i+20)]))
        break
