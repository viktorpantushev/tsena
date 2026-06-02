#!/usr/bin/env python3
"""
Orchestrator with Task Breaker integration.

This demonstrates how the task breaker can be integrated into the orchestrator
workflow. An LLM can: 
1. Analyze a project requirement
2. Use the task breaker service to decompose it
3. Get structured tasks with difficulty ratings
4. Make decisions based on task complexity

Usage (start the task-breaker service in another terminal):
  python3 ollama_orchestrator/tools/task_breaker_service.py

Then run this script:
  python3 ollama_orchestrator/orchestrator_with_task_breaker.py \\
    --prompt "Build a REST API with authentication and database"
"""

from __future__ import annotations

import os
import subprocess
import urllib.parse
import urllib.request
import json
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=None)
def ollama_supports_flag(flag: str) -> bool:
    """Check if ollama CLI supports a specific flag."""
    proc = subprocess.run(["ollama", "run", "--help"], capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    help_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return flag in help_text


def run_ollama(
    model: str,
    prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """Run ollama with a prompt and return output."""
    cmd = ["ollama", "run", model]
    if temperature is not None and ollama_supports_flag("--temperature"):
        cmd += ["--temperature", str(temperature)]
    if max_tokens is not None and ollama_supports_flag("--max-tokens"):
        cmd += ["--max-tokens", str(max_tokens)]
    cmd.append(prompt)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama CLI error: {proc.stderr.strip()}")
    return proc.stdout


def call_task_breaker(
    task_description: str,
    model: str = "qwen2.5:3b",
    base_url: str = "http://127.0.0.1:5001",
    max_retries: int = 3,
) -> dict:
    """
    Call the task breaker service via HTTP.

    Args:
        task_description: The task to break down
        model: The ollama model to use
        base_url: Base URL of the task breaker service
        max_retries: Maximum retries on failure

    Returns:
        Dictionary containing the task breakdown
    """
    url = f"{base_url}/break-task"
    request_data = {
        "task": task_description,
        "model": model,
        "temperature": 0.3,
        "max_retries": max_retries,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(request_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Failed to call task breaker service at {url}: {e}\n"
            "Make sure to start the service: "
            "python3 ollama_orchestrator/tools/task_breaker_service.py"
        )


def analyze_tasks_and_plan(
    task_breakdown: dict,
    model: str = "qwen2.5:3b",
) -> str:
    """
    Use the LLM to analyze broken-down tasks and create a plan.

    Args:
        task_breakdown: The result from task_breaker
        model: The ollama model to use

    Returns:
        LLM's analysis and planning recommendation
    """
    tasks_summary = "\n".join(
        [
            f"- {task['title']} (Difficulty: {task['difficulty']}/5, "
            f"Est: {task['estimated_hours']}h)"
            for task in task_breakdown["tasks"]
        ]
    )

    prompt = f"""Based on these broken-down tasks:

{tasks_summary}

Total estimated time: {task_breakdown['total_estimated_hours']:.1f} hours
Number of tasks: {task_breakdown['task_count']}

Provide a concise project plan that:
1. Identifies critical path tasks
2. Suggests parallelization opportunities
3. Highlights high-difficulty tasks that need extra review
4. Recommends resource allocation strategy"""

    return run_ollama(model, prompt, temperature=0.5, max_tokens=1000)


def orchestrate(
    project_description: str,
    model: str = "qwen2.5:3b",
    task_breaker_url: str = "http://127.0.0.1:5001",
) -> None:
    """
    Main orchestration flow: describe a project, break it down, and plan it.

    Args:
        project_description: High-level project description
        model: The ollama model to use
        task_breaker_url: URL of the task breaker service
    """
    print(f"\n{'='*80}")
    print(f"PROJECT: {project_description}")
    print(f"{'='*80}\n")

    # Step 1: Break down the task
    print("📋 Breaking down tasks...")
    try:
        task_breakdown = call_task_breaker(
            project_description,
            model=model,
            base_url=task_breaker_url,
        )
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        return

    print(f"✅ Successfully identified {task_breakdown['task_count']} tasks\n")

    # Print tasks
    print("TASKS:")
    print("-" * 80)
    for i, task in enumerate(task_breakdown["tasks"], 1):
        difficulty_bar = "🔴" * task["difficulty"] + "⚪" * (5 - task["difficulty"])
        print(f"\n{i}. {task['title']}")
        print(f"   Difficulty: {difficulty_bar} ({task['difficulty']}/5)")
        print(f"   Estimated: {task['estimated_hours']:.1f} hours")
        print(f"   {task['description']}")
        if task["dependencies"]:
            print(f"   Depends on: {', '.join(task['dependencies'])}")

    # Step 2: Analyze and plan
    print(f"\n{'='*80}")
    print("🤔 Analyzing tasks and creating plan...")
    analysis = analyze_tasks_and_plan(task_breakdown, model=model)

    print(f"\n{'='*80}")
    print("PROJECT PLAN:")
    print("-" * 80)
    print(analysis)
    print(f"{'='*80}\n")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Orchestrate project planning with task breaking and analysis"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Project description or task to plan",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to use. If not provided, uses OLLAMA_MODEL or 'qwen2.5:3b'",
    )
    parser.add_argument(
        "--task-breaker-url",
        default="http://127.0.0.1:5001",
        help="URL of the task breaker service (default: http://127.0.0.1:5001)",
    )

    args = parser.parse_args()
    model = args.model or os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

    orchestrate(
        args.prompt,
        model=model,
        task_breaker_url=args.task_breaker_url,
    )


if __name__ == "__main__":
    main()
