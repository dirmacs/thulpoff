from huggingface_hub import hf_hub_download

readme_path = hf_hub_download(repo_id="allenai/OLMo-7B", filename="README.md", repo_type="model")
with open(readme_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the table and print some rows
for i, line in enumerate(lines):
    if '**OLMo 7B**' in line and 'Llama 7B' in line:
        # Print next 15 lines
        for j in range(i, min(i+15, len(lines))):
            print(f"{j}: {lines[j].rstrip()}")
            if '|' in lines[j]:
                parts = lines[j].split('|')
                if len(parts) > 2:
                    print(f"    -> Benchmark col [1]: '{parts[1].strip()}'")
                    if len(parts) > 6:
                        print(f"    -> OLMo col [6]: '{parts[6].strip()}'")
        break
