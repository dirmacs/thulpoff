# One-Shot Evaluation Extraction Task

Extract evaluation benchmark scores from the Hugging Face model "allenai/OLMo-7B" and save them to a YAML file named `olmo_7b_evaluations.yaml` in the current directory.

## Requirements:

1. Use the hugging-face-evaluation-manager skill to extract evaluation data from the model's README
2. Filter the results to include ONLY the following benchmark types:
   - arc_challenge
   - arc_easy
   - boolq
   - copa
   - hellaswag
   - openbookqa
   - piqa
   - sciq
   - winogrande
   - mmlu
   - truthfulqa
3. Save the output in valid model-index YAML format to `olmo_7b_evaluations.yaml` in the current working directory
4. Do NOT include training hyperparameters, model architecture specs, or random baseline scores
5. Include the source attribution pointing to the model README

The output file should be valid YAML that could be directly added to a model card's metadata section.
