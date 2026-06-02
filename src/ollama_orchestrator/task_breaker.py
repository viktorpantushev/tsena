#!/usr/bin/env python3
"""
Task Breaker: Uses a small LLM to break down high-level tasks into smaller subtasks
and rate the difficulty of each task.

This module leverages ollama to decompose complex tasks into manageable pieces
with difficulty ratings, enabling better task planning and resource allocation.

Usage:
  python3 ollama_orchestrator/task_breaker.py --prompt "Build a real-time chat application"
  python3 ollama_orchestrator/task_breaker.py --prompt "Implement user authentication" --model qwen2.5:3b
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from functools import lru_cache
from typing import Optional
from dataclasses import dataclass


@dataclass
class Task:
    """Represents a single task with difficulty rating."""
    title: str
    description: str
    difficulty: int  # 1-5 scale
    estimated_hours: float
    dependencies: list[str]  # List of task titles this depends on


@dataclass
class TaskBreakdown:
    """Container for broken-down tasks."""
    original_prompt: str
    tasks: list[Task]
    total_estimated_hours: float


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
    """Run ollama with a prompt and return raw output."""
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


def run_ollama_json(
    model: str,
    prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    """Run ollama and parse JSON output."""
    cmd = ["ollama", "run", model]
    cmd += ["--json"]
    if temperature is not None and ollama_supports_flag("--temperature"):
        cmd += ["--temperature", str(temperature)]
    if max_tokens is not None and ollama_supports_flag("--max-tokens"):
        cmd += ["--max-tokens", str(max_tokens)]
    cmd.append(prompt)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama CLI error: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _remove_invalid_control_characters(text: str) -> str:
    """Remove invalid control characters from text."""
    # Remove control characters except common ones (tab, newline, carriage return)
    return re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)


def _parse_plain_language_tasks(text: str) -> list[Task]:
    """
    Parse plain language task breakdown from LLM response.
    
    Supports multiple formats:
    - Numbered lists: 1. Task, 2. Task, etc.
    - Dashes: - Task, - Task, etc.
    - Bullets: • Task, * Task, etc.
    
    Extracts metadata like difficulty, estimated hours, and dependencies.
    Intelligently distinguishes between task titles and metadata lines.
    """
    tasks = []
    lines = text.split('\n')
    
    current_task = None
    task_start_pattern = r'^[\s]*([\d]+\.|[-•*])\s+(.+)$'
    
    # Patterns that indicate a line is metadata/description, not a task title
    metadata_patterns = [
        r'^[\s]*(?:description|description of what)',
        r'^[\s]*difficulty',
        r'^[\s]*(?:estimated|estimated time|time|hours)',
        r'^[\s]*depends?(?:\s+on)?',
        r'^[\s]*prerequisite',
        r'^[\s]*requires',
    ]
    
    def is_metadata_only_line(line: str) -> bool:
        """Check if line is metadata/description line rather than task title."""
        line_lower = line.lower().strip()
        for pattern in metadata_patterns:
            if re.match(pattern, line_lower):
                return True
        return False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line starts a new task
        task_match = re.match(task_start_pattern, line)
        
        # Only treat as new task if it's NOT a metadata-only line
        if task_match and not is_metadata_only_line(line):
            # Save previous task if exists
            if current_task:
                tasks.append(current_task)
            
            # Extract title from the line (remove the bullet/number prefix)
            title = re.sub(r'^[\d]+\.|[-•*]\s*', '', line).strip()
            current_task = Task(
                title=title,
                description="",
                difficulty=3,  # Default to medium
                estimated_hours=1.0,  # Default to 1 hour
                dependencies=[]
            )
        elif current_task:
            # Process metadata or description for current task
            line_lower = line.lower()
            
            # Extract difficulty
            diff_match = re.search(r'difficult(?:y)?:?\s*([1-5])', line_lower)
            if diff_match:
                current_task.difficulty = int(diff_match.group(1))
                continue
            
            # Extract hours/time
            hours_match = re.search(r'(?:est(?:imated)?|time):?\s*([\d.]+)\s*(?:h|hour)', line_lower)
            if hours_match:
                current_task.estimated_hours = float(hours_match.group(1))
                continue
            
            # Extract dependencies
            dep_match = re.search(r'(?:depend(?:s)?\s+on|prerequisite|requires):?\s*(.+?)$', line_lower)
            if dep_match:
                deps_text = dep_match.group(1)
                # Split by commas or 'and'
                deps = re.split(r',\s*|\s+and\s+', deps_text)
                current_task.dependencies = [d.strip() for d in deps if d.strip()]
                continue
            
            # Append to description if it doesn't contain metadata keywords
            if not is_metadata_only_line(line):
                if current_task.description:
                    current_task.description += " " + line
                else:
                    current_task.description = line
    
    # Save last task
    if current_task:
        tasks.append(current_task)
    
    return tasks


def _is_valid_json_string(text: str) -> bool:
    """Check if text contains valid JSON without control character issues."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def break_down_task(
    task_description: str,
    model: str = "qwen2.5:3b",
    temperature: float = 0.3,
    max_retries: int = 3,
) -> TaskBreakdown:
    """
    Break down a high-level task into smaller subtasks with difficulty ratings.
    
    Uses plain language to request task breakdown and parses the response.
    Includes automatic retry logic for handling parsing errors.

    Args:
        task_description: The high-level task to break down
        model: The ollama model to use (default: qwen2.5:3b)
        temperature: Temperature for the LLM (lower = more deterministic)
        max_retries: Maximum number of retries on failure (default: 3)

    Returns:
        TaskBreakdown object containing the decomposed tasks
    
    Raises:
        RuntimeError: If all retries fail
    """
    system_prompt = """You are a task decomposition expert. Break down the given task into smaller, 
manageable subtasks. 

IMPORTANT: Format your response EXACTLY like this example (tasks on consecutive lines, metadata on same logical block):

1. Task Title One
Description of the task and what needs to be done.
Difficulty: 2
Estimated: 3 hours
Depends on: None

2. Task Title Two
Description here.
Difficulty: 4
Estimated: 8 hours
Depends on: Task Title One

For each task, provide:
1. A numbered title (1., 2., etc.)
2. Description (1-2 sentences on next line)
3. Difficulty rating (1=trivial, 2=easy, 3=medium, 4=hard, 5=very hard)
4. Estimated hours to complete
5. Dependencies (which other tasks need to be done first, or "None")

Keep all metadata for a single task in one logical block (no blank lines in between).
Be clear and detailed in your descriptions."""

    # Alternative prompt for retries - emphasizes structured plain language
    retry_prompt = """You are a task decomposition expert. Break down the given task.
Provide output in this EXACT format with clear separation:

1. [Task Title]
[1-2 line description]
Difficulty: [1-5]
Estimated: [number] hours

2. [Next Task Title]
[Description]
Difficulty: [1-5]
Estimated: [number] hours

Rules:
- Each task starts with a number and dot
- Difficulty is a number 1-5
- Estimated is just the number and 'hours' keyword
- Keep descriptions concise
- Be thorough with task breakdown"""

    prompt = f"""{system_prompt}

Task to break down:
{task_description}"""

    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Adjust temperature slightly on retries for more variation
            current_temp = temperature + (attempt * 0.1)
            
            # Use different prompt on retries
            current_prompt = prompt if attempt == 0 else f"""{retry_prompt}

Task to break down:
{task_description}"""
            
            # Get response in plain text mode
            text_response = run_ollama(
                model,
                current_prompt,
                temperature=current_temp,
                max_tokens=2000,
            )
            
            # Clean invalid control characters
            text_response = _remove_invalid_control_characters(text_response)
            
            # Parse the plain language response into tasks
            tasks = _parse_plain_language_tasks(text_response)
            
            if not tasks:
                raise ValueError("No tasks could be parsed from the response")
            
            # Calculate total estimated hours
            total_estimated_hours = sum(task.estimated_hours for task in tasks)
            
            # Return the breakdown
            return TaskBreakdown(
                original_prompt=task_description,
                tasks=tasks,
                total_estimated_hours=total_estimated_hours,
            )

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                prompt_type = "structured" if attempt == 0 else "more explicit"
                print(f"⚠️  Attempt {attempt + 1} failed ({prompt_type} prompt next): {str(e)[:80]}... Retrying...", flush=True)
            else:
                print(f"❌ All {max_retries} attempts failed", flush=True)
    
    # All retries failed
    raise RuntimeError(
        f"Failed to break down task after {max_retries} attempts. "
        f"Last error: {str(last_error)}"
    ) from last_error


def format_task_breakdown(breakdown: TaskBreakdown) -> str:
    """Format task breakdown for pretty printing."""
    output = []
    output.append(f"Task Breakdown: {breakdown.original_prompt}")
    output.append(f"Total Estimated Hours: {breakdown.total_estimated_hours:.1f}")
    output.append("-" * 80)

    for i, task in enumerate(breakdown.tasks, 1):
        difficulty_indicator = "🔴" * task.difficulty + "⚪" * (5 - task.difficulty)
        output.append(f"\n{i}. {task.title}")
        output.append(f"   Difficulty: {difficulty_indicator} ({task.difficulty}/5)")
        output.append(f"   Estimated: {task.estimated_hours:.1f} hours")
        output.append(f"   Description: {task.description}")
        if task.dependencies:
            output.append(f"   Dependencies: {', '.join(task.dependencies)}")

    return "\n".join(output)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Break down a task into subtasks with difficulty ratings"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="The task description to break down",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name to use. If not provided, uses OLLAMA_MODEL or 'qwen2.5:3b'",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Temperature for the LLM (default: 0.3)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries on parsing failure (default: 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text",
    )

    args = parser.parse_args()
    model = args.model or os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

    print(f"Breaking down task using model: {model}")
    breakdown = break_down_task(
        args.prompt,
        model=model,
        temperature=args.temperature,
        max_retries=args.max_retries,
    )

    if args.json:
        output = {
            "original_prompt": breakdown.original_prompt,
            "total_estimated_hours": breakdown.total_estimated_hours,
            "tasks": [
                {
                    "title": task.title,
                    "description": task.description,
                    "difficulty": task.difficulty,
                    "estimated_hours": task.estimated_hours,
                    "dependencies": task.dependencies,
                }
                for task in breakdown.tasks
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_task_breakdown(breakdown))


if __name__ == "__main__":
    main()
