#!/usr/bin/env python3
"""
Task Breaker Demo Script

This script demonstrates various ways to use the Task Breaker feature.
Run this to see examples of task decomposition in action.

Usage:
  python3 ollama_orchestrator/examples/task_breaker_demo.py

For orchestrator integration:
  1. In one terminal: python3 ollama_orchestrator/tools/task_breaker_service.py
  2. In another: python3 ollama_orchestrator/examples/task_breaker_demo.py --with-service
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_breaker import break_down_task, format_task_breakdown


def demo_simple_breakdown():
    """Demo 1: Simple task breakdown"""
    print("\n" + "=" * 80)
    print("DEMO 1: Simple Task Breakdown")
    print("=" * 80)

    task = "Create a user authentication system"
    print(f"\nInput: {task}\n")

    try:
        # Will automatically retry up to 3 times if invalid control characters are encountered
        breakdown = break_down_task(task, model="qwen2.5:3b", temperature=0.3, max_retries=3)
        print(format_task_breakdown(breakdown))
    except Exception as e:
        print(f"Error: {e}")


def demo_complex_project():
    """Demo 2: Complex project breakdown"""
    print("\n" + "=" * 80)
    print("DEMO 2: Complex Project Breakdown")
    print("=" * 80)

    task = """Build a real-time multiplayer gaming platform with:
    - User accounts and authentication
    - Matchmaking system
    - Real-time game state synchronization
    - Chat and messaging
    - Leaderboards and statistics"""

    print(f"\nInput: {task}\n")

    try:
        breakdown = break_down_task(task, model="qwen2.5:3b", temperature=0.3)
        print(format_task_breakdown(breakdown))

        # Analyze the breakdown
        print("\n" + "-" * 80)
        print("ANALYSIS:")
        print("-" * 80)
        high_difficulty = [t for t in breakdown.tasks if t.difficulty >= 4]
        no_deps = [t for t in breakdown.tasks if not t.dependencies]

        print(f"Total tasks: {len(breakdown.tasks)}")
        print(f"Total estimated time: {breakdown.total_estimated_hours:.1f} hours")
        print(f"High difficulty tasks ({len(high_difficulty)}): {', '.join([t.title for t in high_difficulty])}")
        print(f"Can start immediately ({len(no_deps)}): {', '.join([t.title for t in no_deps])}")

    except Exception as e:
        print(f"Error: {e}")


def demo_data_engineering():
    """Demo 3: Data engineering project"""
    print("\n" + "=" * 80)
    print("DEMO 3: Data Engineering Project")
    print("=" * 80)

    task = """Implement a data pipeline that:
    1. Ingests data from multiple APIs
    2. Validates and cleans the data
    3. Performs feature engineering
    4. Trains ML models
    5. Generates reports"""

    print(f"\nInput: {task}\n")

    try:
        breakdown = break_down_task(task, model="qwen2.5:3b", temperature=0.3)

        # Print with custom formatting
        print(f"Project: {breakdown.original_prompt[:50]}...")
        print(f"Tasks to complete: {len(breakdown.tasks)}")
        print(f"Time estimate: {breakdown.total_estimated_hours:.1f} hours (~{breakdown.total_estimated_hours/8:.1f} days @ 8h/day)")

        print("\nTasks by difficulty:")
        for difficulty_level in range(1, 6):
            tasks_at_level = [t for t in breakdown.tasks if t.difficulty == difficulty_level]
            if tasks_at_level:
                print(f"\nDifficulty {difficulty_level}: {len(tasks_at_level)} task(s)")
                for task in tasks_at_level:
                    print(f"  • {task.title} ({task.estimated_hours}h)")

    except Exception as e:
        print(f"Error: {e}")


def demo_service_integration():
    """Demo 4: Service integration example"""
    print("\n" + "=" * 80)
    print("DEMO 4: Task Breaker Service Integration")
    print("=" * 80)

    import urllib.request
    import json

    task = "Build a REST API for an e-commerce platform"

    print(f"\nInput: {task}")
    print("Calling HTTP service....\n")

    url = "http://127.0.0.1:5001/break-task"
    request_data = {
        "task": task,
        "model": "qwen2.5:3b",
        "temperature": 0.3,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(request_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

            if result.get("status") == "success":
                print(f"✓ Task breaking succeeded!")
                print(f"  Tasks identified: {result['task_count']}")
                print(f"  Total time: {result['total_estimated_hours']:.1f} hours")

                print("\nTask List:")
                for i, task in enumerate(result["tasks"], 1):
                    print(f"  {i}. {task['title']}")
                    print(f"     ├ Difficulty: {task['difficulty']}/5")
                    print(f"     ├ Time: {task['estimated_hours']}h")
                    if task["dependencies"]:
                        print(f"     └ Depends on: {', '.join(task['dependencies'])}")
            else:
                print(f"✗ Error: {result.get('error')}")

    except urllib.error.URLError as e:
        print(f"✗ Service not available: {e}")
        print("  Start the service with: python3 ollama_orchestrator/tools/task_breaker_service.py")


def main():
    """Run all demos or specific demo based on arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Task Breaker Demo")
    parser.add_argument(
        "--demo",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run specific demo (1-4)",
    )
    parser.add_argument(
        "--with-service",
        action="store_true",
        help="Run service integration demo instead of others",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5:3b",
        help="Model to use (default: qwen2.5:3b)",
    )

    args = parser.parse_args()

    if args.with_service:
        demo_service_integration()
    elif args.demo == 1:
        demo_simple_breakdown()
    elif args.demo == 2:
        demo_complex_project()
    elif args.demo == 3:
        demo_data_engineering()
    elif args.demo == 4:
        demo_service_integration()
    else:
        # Run all local demos
        print("\n🚀 Task Breaker Feature Demo")
        print("=" * 80)
        print("This script demonstrates various applications of task breaking.\n")

        demo_simple_breakdown()
        demo_complex_project()
        demo_data_engineering()

        print("\n" + "=" * 80)
        print("DEMO SUMMARY")
        print("=" * 80)
        print("""
✓ Task Breaker Features Demonstrated:
  1. Simple task decomposition
  2. Complex project planning
  3. Data engineering workflows
  4. Service integration (available with --with-service)

📖 For more information, see: ollama_orchestrator/TASK_BREAKER_README.md

🔗 Try service integration:
  Terminal 1: python3 ollama_orchestrator/tools/task_breaker_service.py
  Terminal 2: python3 ollama_orchestrator/examples/task_breaker_demo.py --with-service

🎯 Use in your projects:
  from ollama_orchestrator.task_breaker import break_down_task
  breakdown = break_down_task("Your task description")
        """)


if __name__ == "__main__":
    main()
