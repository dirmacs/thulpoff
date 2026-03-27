#!/usr/bin/env python3
"""
Evaluation runner with iteration support.
"""

import argparse
import asyncio
import contextlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from fast_agent import FastAgent
from fast_agent.mcp.prompts.prompt_load import load_prompt
from fast_agent.session import get_session_manager, reset_session_manager
from test_eval_assertions import (
    ASSERTIONS_TOTAL,
    ValidationResult,
    validate_with_metrics,
)

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "fastagent.config.yaml"
PROMPT_SOURCE = ROOT_DIR / "build_olmo_yaml.md"
AGENTS_SOURCE = ROOT_DIR / "AGENTS.md"
SKILLS_REPO_URL = "https://github.com/huggingface/skills.git"
SKILLS_REPO_COMMIT = "fe044dc129e33aca7c2edc0084f02a7119b4109f"
SKILLS_REPO_CACHE = ROOT_DIR / "skills_repo"
SKILL_NAMES = (
    "hugging-face-evaluation",
    "hugging-face-evaluation-manager",
)
SKILL_MANIFEST_CANDIDATES = [
    Path("skills") / "hugging-face-evaluation" / "SKILL.md",
    Path("hf_model_evaluation")
    / "skills"
    / "hugging-face-evaluation-manager"
    / "SKILL.md",
    Path("hf_model_evaluation") / "skills" / "hugging-face-evaluation" / "SKILL.md",
]

# Files to exclude when copying artifacts into run workspaces
EXCLUDE_FILES = {
    "agent.py",
    "test_eval_assertions.py",
    "fastagent.config.yaml",
    "fastagent.secrets.yaml",
}



default_instruction = """You are a helpful AI Agent.

{{serverInstructions}}

{{agentSkills}}

{{file_silent:AGENTS.md}}

{{env}}

The current date is {{currentDate}}."""


@contextlib.contextmanager
def run_in_workspace(path: Path):
    """Temporarily change the working directory to the given path."""
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def copy_prompt_assets(workspace: Path) -> None:
    """Copy prompt inputs needed by the agent into the workspace."""
    if not PROMPT_SOURCE.exists():
        raise FileNotFoundError(f"Prompt source missing: {PROMPT_SOURCE}")
    if not AGENTS_SOURCE.exists():
        raise FileNotFoundError(f"AGENTS.md missing: {AGENTS_SOURCE}")
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROMPT_SOURCE, workspace / PROMPT_SOURCE.name)
    shutil.copy2(AGENTS_SOURCE, workspace / AGENTS_SOURCE.name)


def _sparse_checkout_paths() -> list[str]:
    paths = []
    for candidate in SKILL_MANIFEST_CANDIDATES:
        paths.append(str(candidate.parent))
    return sorted(set(paths))


def _clone_skills_repo(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)

    subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            SKILLS_REPO_URL,
            str(destination),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    sparse_paths = _sparse_checkout_paths()
    subprocess.run(
        ["git", "-C", str(destination), "sparse-checkout", "init", "--cone"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(destination), "sparse-checkout", "set", *sparse_paths],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(destination), "checkout", SKILLS_REPO_COMMIT],
        check=True,
        capture_output=True,
        text=True,
    )


def _find_skill_manifest(skills_repo_dir: Path) -> Path:
    for candidate in SKILL_MANIFEST_CANDIDATES:
        manifest = skills_repo_dir / candidate
        if manifest.exists():
            return manifest

    for manifest in skills_repo_dir.rglob("SKILL.md"):
        try:
            content = manifest.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name in SKILL_NAMES:
            if f"name: {name}" in content or f'name: "{name}"' in content:
                return manifest

    candidates_text = "\n".join(f"- {candidate}" for candidate in SKILL_MANIFEST_CANDIDATES)
    raise FileNotFoundError(
        "Expected skill manifest not found in cloned skills repo. "
        f"Checked candidates:\n{candidates_text}\n"
        f"Repo: {SKILLS_REPO_URL}"
    )


def ensure_skills_repo() -> Path:
    """Ensure the skills repo is available locally (sparse checkout)."""
    destination = SKILLS_REPO_CACHE
    if destination.exists():
        try:
            subprocess.run(
                ["git", "-C", str(destination), "rev-parse", "--git-dir"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            shutil.rmtree(destination)

    if not destination.exists():
        _clone_skills_repo(destination)
    else:
        sparse_paths = _sparse_checkout_paths()
        subprocess.run(
            ["git", "-C", str(destination), "sparse-checkout", "set", *sparse_paths],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(destination), "checkout", SKILLS_REPO_COMMIT],
            check=True,
            capture_output=True,
            text=True,
        )

    return _find_skill_manifest(destination)


def prepare_skills_directory(
    manifest_path: Path,
    destination: Path,
) -> Path:
    """Create a filtered skills directory containing only the target skill."""
    if destination.exists():
        shutil.rmtree(destination)

    skill_dir = manifest_path.parent
    target_dir = destination / skill_dir.name
    ignore = shutil.ignore_patterns(".git", ".venv", "__pycache__")
    shutil.copytree(skill_dir, target_dir, ignore=ignore)
    return destination



def build_fast_agent(environment_dir: Path, skills_manifest_dir: Path) -> FastAgent:
    """Create a fast-agent  instance configured for a single run."""
    fast = FastAgent(
        "fast-agent example",
        ignore_unknown_args=True,
        config_path=str(CONFIG_PATH),
        environment_dir=environment_dir,
        skills_directory=[skills_manifest_dir],
    )

    @fast.agent(
        name="eval_skill",
        servers=["huggingface"],
        instruction=default_instruction,
    )
    async def eval_skill():
        return None

    return fast


def _extract_model_arg(unknown: list[str]) -> str | None:
    for idx, arg in enumerate(unknown):
        if arg.startswith("--model="):
            return arg.split("=", 1)[1]
        if arg in {"--model", "--model-name"} and idx + 1 < len(unknown):
            return unknown[idx + 1]
    return None


def parse_args() -> tuple[argparse.Namespace, str | None]:
    """Parse command line arguments, ignoring unknown args (e.g., --model for FastAgent)."""
    parser = argparse.ArgumentParser(description="Run evaluation iterations")
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of iterations to run (default: 1)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="olmo_7b_evaluations.yaml",
        help=(
            "Name of the output YAML file to validate "
            "(default: olmo_7b_evaluations.yaml)"
        ),
    )
    args, unknown = parser.parse_known_args()
    model_name = _extract_model_arg(unknown)
    return args, model_name


def write_run_metadata(run_folder: Path, model_name: str | None, output_filename: str) -> None:
    payload = {
        "model": model_name or "",
        "output_file": output_filename,
    }
    path = run_folder / "run_metadata.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def main():
    args, model_name = parse_args()
    num_runs = args.runs
    output_filename = args.output_file

    # Create timestamped batch folder for artifacts
    batch_id = datetime.now().strftime("%Y_%m_%d_%H_%M")
    batch_folder = (ROOT_DIR / "runs" / batch_id).resolve()
    batch_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Starting evaluation batch: {num_runs} run(s)")
    print(f"Batch ID: {batch_id}")
    print(f"Artifacts folder: {batch_folder}")
    print(f"{'='*60}\n")

    results: list[ValidationResult] = []

    for i in range(1, num_runs + 1):
        print(f"\n--- Run {i}/{num_runs} ---")

        run_folder = batch_folder / f"run_{i}"
        run_folder.mkdir(exist_ok=True)
        workspace = (run_folder / "workspace").resolve()
        env_dir = run_folder.resolve()
        skills_dir = (workspace / "skills").resolve()

        copy_prompt_assets(workspace)
        manifest_path = ensure_skills_repo()
        skills_manifest_dir = prepare_skills_directory(manifest_path, skills_dir)
        write_run_metadata(run_folder, model_name, output_filename)

        try:
            fast = build_fast_agent(env_dir, skills_manifest_dir)
            async with fast.run() as agent:
                eval_agent = agent.eval_skill
                session_root = batch_folder / "sessions" / f"run_{i}"
                session_root.mkdir(parents=True, exist_ok=True)
                reset_session_manager()
                manager = get_session_manager()
                manager.base_dir = session_root
                manager.create_session(
                    metadata={
                        "batch_id": batch_id,
                        "run_number": i,
                        "output_file": output_filename,
                    }
                )

                with run_in_workspace(workspace):
                    prompt_path = Path(PROMPT_SOURCE.name)
            #       await agent.interactive()
                    await eval_agent.generate(load_prompt(prompt_path))

            output_path = workspace / output_filename
            validation: ValidationResult = validate_with_metrics(output_path)

            status = "PASSED" if validation.passed else "FAILED"
            print(
                f"Run {i}: {status} ("
                f"{validation.assertions_passed}/{validation.assertions_total} assertions)"
            )

        except Exception as e:
            print(f"Run {i}: ERROR - {e}")
            validation = ValidationResult(
                passed=False,
                assertions_passed=0,
                assertions_total=ASSERTIONS_TOTAL,
                metrics_count=0,
                benchmarks_found=[],
                error_message=str(e),
            )

        moved = []
        for pattern in ["*.yaml", "*.py"]:
            for f in Path(".").glob(pattern):
                if f.name in EXCLUDE_FILES:
                    continue
                dest = run_folder / f.name
                shutil.move(str(f), str(dest))
                moved.append(f.name)
        if moved:
            print(f"Collected artifacts from repo root: {moved}")

        results.append(validation)

    print(f"\n{'='*60}")
    print("BATCH COMPLETE")
    print(f"{'='*60}")
    passed_count = sum(1 for r in results if r.passed)
    print(f"Passed: {passed_count}/{num_runs}")
    print(f"Batch ID: {batch_id}")
    print(f"Artifacts: {batch_folder}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
