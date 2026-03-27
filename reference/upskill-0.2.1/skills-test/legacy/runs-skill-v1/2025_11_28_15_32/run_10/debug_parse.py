#!/usr/bin/env python3
from huggingface_hub import hf_hub_download

readme_path = hf_hub_download(repo_id="allenai/OLMo-7B", filename="README.md", repo_type="model")
with open(readme_path, 'r', encoding='utf-8') as f:
    readme_text = f.read()

lines = readme_text.split('\n')

for i, line in enumerate(lines):
    if '**OLMo 7B**' in line and 'Llama 7B' in line:
        print(f"Line {i}: {repr(line)}")
        parts = line.split('|')
        print(f"Number of parts: {len(parts)}")
        for idx, part in enumerate(parts):
            print(f"  [{idx}]: {repr(part.strip())}")
        
        # Now check the next few data rows
        print("\nNext 5 lines:")
        for j in range(i+1, min(i+6, len(lines))):
            if '|' in lines[j]:
                print(f"Line {j}: {repr(lines[j])}")
                parts = lines[j].split('|')
                print(f"  Parts: {len(parts)}")
                if len(parts) > 5:
                    print(f"  Benchmark: {parts[0].strip()}")
                    print(f"  OLMo value (idx 5): {parts[5].strip()}")
        break
