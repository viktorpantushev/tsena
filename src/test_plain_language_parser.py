#!/usr/bin/env python3
"""
Test the new plain language parsing feature
"""

from ollama_orchestrator.task_breaker import _parse_plain_language_tasks, Task

# Test case 1: Simple plain language output from LLM
test_response_1 = """
1. Set up project structure
Create project directory and install dependencies. This is the foundation.
Difficulty: 1
Estimated: 1.5 hours

2. Implement database schema
Design and create database tables for users and posts.
Difficulty: 3
Estimated: 4 hours
Depends on: Set up project structure

3. Build API endpoints
Create REST API for CRUD operations.
Difficulty: 4
Estimated: 8 hours
Depends on: Implement database schema
"""

# Test case 2: Different format variations
test_response_2 = """
- Task One
Simple clean-up tasks.
difficulty: 2
estimated: 2 hours

- Task Two
Build the main feature.
difficulty: 4
estimated: 6 hours
"""

# Test case 3: Bullet points
test_response_3 = """
• Authentication System
Implement user login and registration.
Difficulty: 3
Estimated: 5 hours

• Payment Integration
Integrate payment gateway.
Difficulty: 4
Estimated: 6 hours
depends on: Authentication System
"""


def test_parser():
    print("🧪 Testing Plain Language Parser\n")
    
    # Test 1
    print("Test 1: Numbered list format")
    print("-" * 60)
    tasks = _parse_plain_language_tasks(test_response_1)
    for task in tasks:
        print(f"✓ {task.title}")
        print(f"  Difficulty: {task.difficulty}/5, Time: {task.estimated_hours}h")
        if task.dependencies:
            print(f"  Depends on: {task.dependencies}")
    assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"
    assert tasks[0].difficulty == 1
    assert tasks[1].estimated_hours == 4
    print("✅ Test 1 passed!\n")
    
    # Test 2
    print("Test 2: Dash format")
    print("-" * 60)
    tasks = _parse_plain_language_tasks(test_response_2)
    for task in tasks:
        print(f"✓ {task.title}")
        print(f"  Difficulty: {task.difficulty}/5, Time: {task.estimated_hours}h")
    assert len(tasks) == 2, f"Expected 2 tasks, got {len(tasks)}"
    print("✅ Test 2 passed!\n")
    
    # Test 3
    print("Test 3: Bullet point format")
    print("-" * 60)
    tasks = _parse_plain_language_tasks(test_response_3)
    for task in tasks:
        print(f"✓ {task.title}")
        print(f"  Difficulty: {task.difficulty}/5, Time: {task.estimated_hours}h")
        if task.dependencies:
            print(f"  Depends on: {task.dependencies}")
    assert len(tasks) == 2, f"Expected 2 tasks, got {len(tasks)}"
    assert len(tasks[1].dependencies) > 0, "Second task should have dependencies"
    print("✅ Test 3 passed!\n")
    
    print("=" * 60)
    print("🎉 All parser tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_parser()
