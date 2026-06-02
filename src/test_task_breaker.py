#!/usr/bin/env python3
"""
Quick test script to try the Task Breaker feature
Run this directly to see the feature in action
"""

from ollama_orchestrator.task_breaker import break_down_task, format_task_breakdown


def test_simple_task():
    """Test 1: Simple task breakdown"""
    print("\n" + "=" * 80)
    print("TEST 1: Simple Task Breakdown")
    print("=" * 80)
    
    task = "Create a login page with email and password validation"
    print(f"Input: {task}\n")
    
    try:
        breakdown = break_down_task(task, max_retries=3)
        print(format_task_breakdown(breakdown))
        print("✅ Success!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_complex_project():
    """Test 2: Complex project with multiple requirements"""
    print("\n" + "=" * 80)
    print("TEST 2: Complex Project Breakdown")
    print("=" * 80)
    
    task = """Build a mobile app todo list with:
    - User authentication
    - Create/edit/delete todos
    - Mark todos complete
    - Due date reminders
    - Sync across devices"""
    
    print(f"Input: {task}\n")
    
    try:
        breakdown = break_down_task(task, max_retries=3)
        print(format_task_breakdown(breakdown))
        
        # Analysis
        print("\n" + "-" * 80)
        print("ANALYSIS:")
        print("-" * 80)
        easy = [t for t in breakdown.tasks if t.difficulty <= 2]
        hard = [t for t in breakdown.tasks if t.difficulty >= 4]
        print(f"Total tasks: {len(breakdown.tasks)}")
        print(f"Total time: {breakdown.total_estimated_hours:.1f} hours")
        print(f"Easy tasks: {len(easy)}")
        print(f"Hard tasks: {len(hard)}")
        
        print("✅ Success!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_json_output():
    """Test 3: Get JSON output for programmatic use"""
    print("\n" + "=" * 80)
    print("TEST 3: JSON Output Test")
    print("=" * 80)
    
    task = "Set up a database with user management"
    print(f"Input: {task}\n")
    
    try:
        import json
        breakdown = break_down_task(task, max_retries=3)
        
        # Convert to JSON-like dict
        output = {
            "original_prompt": breakdown.original_prompt,
            "total_estimated_hours": breakdown.total_estimated_hours,
            "task_count": len(breakdown.tasks),
            "tasks": [
                {
                    "title": t.title,
                    "description": t.description,
                    "difficulty": t.difficulty,
                    "estimated_hours": t.estimated_hours,
                    "dependencies": t.dependencies,
                }
                for t in breakdown.tasks
            ]
        }
        
        print(json.dumps(output, indent=2))
        print("\n✅ Success!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_with_custom_model():
    """Test 4: Use a different model if available"""
    print("\n" + "=" * 80)
    print("TEST 4: Custom Model Test")
    print("=" * 80)
    
    task = "Build a REST API for a blog platform"
    print(f"Input: {task}")
    print("Model: mistral:7b (if available)\n")
    
    try:
        # Try with mistral if available, fall back to qwen
        breakdown = break_down_task(
            task,
            model="mistral:7b",
            temperature=0.4,
            max_retries=2
        )
        print(format_task_breakdown(breakdown))
        print("✅ Success with mistral:7b!")
        return True
    except Exception as e:
        print(f"⚠️  mistral:7b not available or failed, trying qwen2.5:3b...")
        try:
            breakdown = break_down_task(
                task,
                model="qwen2.5:3b",
                max_retries=3
            )
            print(format_task_breakdown(breakdown))
            print("✅ Success with qwen2.5:3b!")
            return True
        except Exception as e2:
            print(f"❌ Error: {e2}")
            return False


def main():
    """Run all tests"""
    print("\n🚀 Task Breaker - Quick Test Suite")
    print("=" * 80)
    
    results = []
    
    # Test 1
    results.append(("Simple Task", test_simple_task()))
    
    # Test 2
    results.append(("Complex Project", test_complex_project()))
    
    # Test 3
    results.append(("JSON Output", test_json_output()))
    
    # Test 4
    results.append(("Custom Model", test_with_custom_model()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
