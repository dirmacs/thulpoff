# thulpoff Examples

This document provides detailed examples of thulpoff workflows.

## Example 1: CUDA Kernel Optimization Skill

This example demonstrates creating a skill for writing optimized CUDA matrix multiplication kernels.

### Step 1: Generate the Skill

```bash
thulpoff generate \
  --task "Write an optimized CUDA kernel for matrix multiplication using shared memory tiling. The kernel should handle arbitrary matrix sizes and achieve good occupancy. Include proper error handling and a host function that allocates memory and launches the kernel." \
  --name cuda-matmul \
  --model claude-sonnet-4-20250514 \
  --test-cases 10 \
  --include-references \
  --verbose
```

**Output:**

```
Generating skill: cuda-matmul
Teacher model: claude-sonnet-4-20250514 (Anthropic)

[1/4] Running teacher session...
  Turn 1: Analyzing requirements...
  Turn 2: Designing kernel architecture...
  Turn 3: Implementing shared memory tiling...
  Turn 4: Adding edge case handling...
  Turn 5: Optimizing memory access patterns...
  Turn 6: Creating host wrapper function...
  Session complete: 6 turns, 4,521 tokens

[2/4] Extracting skill...
  Identified 5 key patterns
  Generated skill content (2,340 chars)

[3/4] Generating test cases...
  Test 1: Basic 1024x1024 multiplication
  Test 2: Non-power-of-2 dimensions (1000x1500)
  Test 3: Edge case: single element matrix
  Test 4: Large matrix (4096x4096)
  Test 5: Rectangular matrix (512x2048)
  Test 6: Performance benchmark
  Test 7: Numerical accuracy check
  Test 8: Memory alignment edge case
  Test 9: Multiple concurrent kernels
  Test 10: Error handling validation
  Generated 10 test cases

[4/4] Extracting references...
  Extracted: kernel_template.cu (45 lines)
  Extracted: host_wrapper.cu (32 lines)

Skill saved to: ./skills/cuda-matmul/

Summary:
  - SKILL.md: 2,340 chars
  - Test cases: 10
  - References: 2 files
  - Total tokens: 5,892
  - Duration: 34.2s
```

### Generated SKILL.md

```markdown
---
name: cuda-matmul
description: Generate optimized CUDA kernels for matrix multiplication using shared memory tiling
---

# CUDA Matrix Multiplication Optimization

When asked to write a CUDA matrix multiplication kernel, follow these guidelines:

## Architecture Decisions

1. **Shared Memory Tiling**
   - Use tile sizes of 16x16 or 32x32 (balance between occupancy and shared memory)
   - Load tiles collaboratively with all threads in a block
   - Use `__syncthreads()` after loading each tile

2. **Memory Access Patterns**
   - Ensure coalesced global memory reads (consecutive threads read consecutive addresses)
   - Avoid bank conflicts in shared memory (32-bank architecture)
   - Use `float4` or `float2` for vectorized loads when possible

3. **Thread Block Configuration**
   - Use 2D thread blocks matching tile size
   - Calculate grid dimensions to cover output matrix
   - Handle edge cases for matrices not divisible by tile size

## Implementation Template

```cuda
#define TILE_SIZE 16

__global__ void matmul_tiled(
    const float* __restrict__ A,
    const float* __restrict__ B,
    float* __restrict__ C,
    int M, int N, int K
) {
    __shared__ float As[TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[TILE_SIZE][TILE_SIZE];
    
    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;
    
    float sum = 0.0f;
    
    for (int t = 0; t < (K + TILE_SIZE - 1) / TILE_SIZE; t++) {
        // Load tiles with bounds checking
        int aCol = t * TILE_SIZE + threadIdx.x;
        int bRow = t * TILE_SIZE + threadIdx.y;
        
        As[threadIdx.y][threadIdx.x] = (row < M && aCol < K) 
            ? A[row * K + aCol] : 0.0f;
        Bs[threadIdx.y][threadIdx.x] = (bRow < K && col < N) 
            ? B[bRow * N + col] : 0.0f;
        
        __syncthreads();
        
        #pragma unroll
        for (int i = 0; i < TILE_SIZE; i++) {
            sum += As[threadIdx.y][i] * Bs[i][threadIdx.x];
        }
        
        __syncthreads();
    }
    
    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}
```

## Host Function

Always provide a host function that:
1. Allocates device memory with `cudaMalloc`
2. Copies input data with `cudaMemcpy`
3. Configures and launches the kernel
4. Copies results back
5. Frees device memory
6. Checks for errors at each step using `cudaGetLastError()`

## Performance Considerations

- **Occupancy**: Aim for 50%+ occupancy, check with `cudaOccupancyMaxPotentialBlockSize`
- **Register Usage**: Keep register usage under 32 per thread for good occupancy
- **Shared Memory**: Don't exceed 48KB per block on most GPUs
- **Loop Unrolling**: Use `#pragma unroll` for the inner accumulation loop
```

### Step 2: Evaluate with a Student Model

```bash
thulpoff eval \
  --skill cuda-matmul \
  --model claude-3-5-haiku-20241022 \
  --baseline \
  --verbose
```

**Output:**

```
Evaluating skill: cuda-matmul
Student model: claude-3-5-haiku-20241022 (Anthropic)
Mode: Baseline comparison enabled

Running 10 test cases...

Test 1: Basic 1024x1024 multiplication
  Baseline: PASS (score: 0.85, 3 turns, 1,234 tokens)
  With skill: PASS (score: 0.95, 2 turns, 892 tokens)

Test 2: Non-power-of-2 dimensions (1000x1500)
  Baseline: FAIL (score: 0.40, 5 turns, 2,156 tokens)
    Error: Missing bounds checking, kernel crashes
  With skill: PASS (score: 0.90, 2 turns, 945 tokens)

Test 3: Edge case: single element matrix
  Baseline: PASS (score: 0.70, 2 turns, 876 tokens)
  With skill: PASS (score: 0.95, 1 turn, 654 tokens)

[... tests 4-10 ...]

Evaluation Summary:
┌─────────────────────────────────────────────────────────────┐
│                    Evaluation Results                        │
├───────────────────┬────────────────┬─────────────────────────┤
│ Metric            │ Baseline       │ With Skill              │
├───────────────────┼────────────────┼─────────────────────────┤
│ Pass Rate         │ 40% (4/10)     │ 90% (9/10)              │
│ Average Score     │ 0.52           │ 0.89                    │
│ Avg Tokens        │ 1,856          │ 812                     │
│ Avg Turns         │ 4.2            │ 1.8                     │
└───────────────────┴────────────────┴─────────────────────────┘

Improvement: +50% pass rate, +37 score points, -56% tokens

Run saved: runs/cuda-matmul/run-abc123.json
```

### Step 3: View Results

```bash
thulpoff list --with-results
```

**Output:**

```
┌─────────────────┬────────────┬────────────────┬─────────────┬─────────────┐
│ Name            │ Test Cases │ Baseline Pass  │ Skill Pass  │ Improvement │
├─────────────────┼────────────┼────────────────┼─────────────┼─────────────┤
│ cuda-matmul     │ 10         │ 40%            │ 90%         │ +50%        │
└─────────────────┴────────────┴────────────────┴─────────────┴─────────────┘
```

---

## Example 2: Local Model Evaluation

Evaluate skills with local models via Ollama.

### Prerequisites

```bash
# Start Ollama with a coding model
ollama pull qwen2.5-coder:32b
ollama serve
```

### Evaluate

```bash
thulpoff eval \
  --skill cuda-matmul \
  --model qwen2.5-coder:32b \
  --provider openai-compat \
  --base-url http://localhost:11434/v1 \
  --baseline
```

**Output:**

```
Evaluating skill: cuda-matmul
Student model: qwen2.5-coder:32b (openai-compat @ localhost:11434)
Mode: Baseline comparison enabled

Running 10 test cases...
[Progress bar]

Evaluation Summary:
┌───────────────────┬────────────────┬─────────────────────────┐
│ Metric            │ Baseline       │ With Skill              │
├───────────────────┼────────────────┼─────────────────────────┤
│ Pass Rate         │ 30% (3/10)     │ 70% (7/10)              │
│ Average Score     │ 0.45           │ 0.78                    │
└───────────────────┴────────────────┴─────────────────────────┘

Improvement: +40% pass rate
```

---

## Example 3: NVIDIA NIM Evaluation

Evaluate with NVIDIA-hosted models.

```bash
export NVIDIA_API_KEY="nvapi-xxx"

thulpoff eval \
  --skill cuda-matmul \
  --model meta/llama-3.1-70b-instruct \
  --provider openai-compat \
  --base-url https://integrate.api.nvidia.com/v1 \
  --baseline
```

---

## Example 4: Multi-Model Comparison

Compare multiple student models at once.

```bash
thulpoff eval \
  --skill cuda-matmul \
  --model claude-3-5-haiku-20241022 \
  --model gpt-4o-mini \
  --baseline \
  --output comparison.json
```

Then analyze the results:

```bash
cat comparison.json | jq '.summary'
```

---

## Example 5: Skill Refinement

After evaluation reveals failures, refine the skill.

### View Failures

```bash
thulpoff runs --skill cuda-matmul --run abc123
```

**Output:**

```
Run: abc123
Skill: cuda-matmul
Model: claude-3-5-haiku-20241022

Failed Test Cases:
1. Test 10: Error handling validation
   Expected: Proper CUDA error checking
   Actual: No cudaGetLastError() calls
   Scorer: "The kernel lacks error handling..."

Skill Areas to Improve:
- Error handling section needs more emphasis
- Could add explicit code example for error checking
```

### Refine

```bash
thulpoff refine --skill cuda-matmul --run abc123 --verbose
```

**Output:**

```
Analyzing 1 failure(s) from run abc123...

Proposed changes:
1. Add explicit error checking code example
2. Emphasize cudaGetLastError() in guidelines
3. Add error handling test pattern

Preview of updated SKILL.md:
[diff output]

Apply changes? [y/N] y

Skill updated: ./skills/cuda-matmul/SKILL.md
Backup saved: ./skills/cuda-matmul/SKILL.md.bak
```

### Re-evaluate

```bash
thulpoff eval --skill cuda-matmul --model claude-3-5-haiku-20241022
```

---

## Example 6: Python Web Scraper Skill

A different domain: async Python programming.

### Generate

```bash
thulpoff generate \
  --task "Write a production-ready async Python web scraper using aiohttp and BeautifulSoup. It should handle rate limiting, retries with exponential backoff, respect robots.txt, extract structured data, and handle common errors gracefully. Include proper logging and type hints." \
  --name py-async-scraper \
  --model claude-sonnet-4-20250514 \
  --test-cases 8
```

### Generated SKILL.md Preview

```markdown
---
name: py-async-scraper
description: Build production-ready async Python web scrapers with proper error handling
---

# Async Python Web Scraper

When asked to write an async web scraper in Python...

## Core Architecture

1. **Session Management**
   - Use `aiohttp.ClientSession` as context manager
   - Configure connection pool limits
   - Set appropriate timeouts

2. **Rate Limiting**
   - Implement token bucket or sliding window
   - Use `asyncio.Semaphore` for concurrency control
   - Add delay between requests to same domain

3. **Retry Logic**
   - Exponential backoff with jitter
   - Distinguish retryable vs non-retryable errors
   - Set maximum retry attempts

[...]
```

---

## Example 7: Batch Processing

Process multiple tasks in batch.

### Create Tasks File

```json
// tasks.json
[
  {
    "name": "rust-error-handling",
    "task": "Implement comprehensive error handling in Rust using thiserror and anyhow..."
  },
  {
    "name": "go-concurrency",
    "task": "Write concurrent Go code using goroutines, channels, and sync primitives..."
  },
  {
    "name": "typescript-validation",
    "task": "Create runtime type validation in TypeScript using Zod schemas..."
  }
]
```

### Batch Generate

```bash
# Generate all skills (serially)
for task in $(cat tasks.json | jq -c '.[]'); do
  name=$(echo $task | jq -r '.name')
  desc=$(echo $task | jq -r '.task')
  thulpoff generate --task "$desc" --name "$name"
done
```

### Batch Evaluate

```bash
thulpoff eval --skill rust-error-handling --model claude-3-5-haiku-20241022 &
thulpoff eval --skill go-concurrency --model claude-3-5-haiku-20241022 &
thulpoff eval --skill typescript-validation --model claude-3-5-haiku-20241022 &
wait
```

---

## Example 8: CI Integration

Add skill evaluation to CI/CD pipeline.

### GitHub Actions Workflow

```yaml
# .github/workflows/skill-eval.yml
name: Skill Evaluation

on:
  push:
    paths:
      - 'skills/**'
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install thulpoff
        run: cargo install thulpoff
      
      - name: Evaluate skills
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          for skill in $(thulpoff list --format json | jq -r '.[].name'); do
            thulpoff eval \
              --skill "$skill" \
              --model claude-3-5-haiku-20241022 \
              --output "results/${skill}.json"
          done
      
      - name: Check pass rates
        run: |
          for result in results/*.json; do
            pass_rate=$(jq '.summary.skill_pass_rate' "$result")
            if (( $(echo "$pass_rate < 0.7" | bc -l) )); then
              echo "FAIL: $result has pass rate $pass_rate"
              exit 1
            fi
          done
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: eval-results
          path: results/
```

---

## Skill Output Structure

All examples produce skills with this structure:

```
skills/
└── skill-name/
    ├── SKILL.md              # Main skill file
    ├── skill_meta.json       # Metadata
    ├── test_cases.json       # Test cases
    └── references/           # Optional
        ├── template.ext
        └── example.ext
```

### skill_meta.json Example

```json
{
  "name": "cuda-matmul",
  "description": "Generate optimized CUDA kernels for matrix multiplication",
  "created_at": "2026-01-29T15:30:00Z",
  "updated_at": "2026-01-29T16:45:00Z",
  "teacher_model": "claude-sonnet-4-20250514",
  "generation_task": "Write an optimized CUDA kernel for matrix multiplication...",
  "test_cases_count": 10,
  "latest_eval": {
    "baseline_pass_rate": 0.40,
    "skill_pass_rate": 0.90,
    "improvement": 0.50,
    "student_model": "claude-3-5-haiku-20241022",
    "evaluated_at": "2026-01-29T16:45:00Z"
  },
  "eval_run_ids": ["abc123", "def456"]
}
```

### test_cases.json Example

```json
[
  {
    "id": "tc-001",
    "prompt": "Write a CUDA kernel to multiply two 1024x1024 matrices",
    "expected_behavior": "Produces correct output, uses shared memory tiling",
    "validation_script": "python validate_cuda.py --size 1024",
    "difficulty": "easy",
    "tags": ["basic", "square-matrix"]
  },
  {
    "id": "tc-002",
    "prompt": "Write a CUDA kernel for 1000x1500 matrix multiplication",
    "expected_behavior": "Handles non-power-of-2 dimensions with bounds checking",
    "difficulty": "medium",
    "tags": ["edge-case", "non-square"]
  }
]
```
