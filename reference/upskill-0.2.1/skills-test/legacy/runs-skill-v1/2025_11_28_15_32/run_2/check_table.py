from huggingface_hub import hf_hub_download

readme_path = hf_hub_download(
    repo_id="allenai/OLMo-7B",
    filename="README.md",
    repo_type="model"
)

with open(readme_path, 'r') as f:
    readme = f.read()

lines = readme.split('\n')

# Find the table
for i, line in enumerate(lines):
    if '**OLMo 7B**' in line and 'ours' in line:
        print(f"Line {i}: {line}")
        # Print next 15 lines
        for j in range(i, min(i+15, len(lines))):
            print(f"{j}: {lines[j]}")
        break
