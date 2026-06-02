#!/usr/bin/env python3
"""
Test script for Task Breaker HTTP Service
Requires the service running: python3 ollama_orchestrator/tools/task_breaker_service.py
"""

import urllib.request
import json
import sys


def test_service(task, model="qwen2.5:3b", max_retries=3):
    """Test the task breaker service via HTTP"""
    url = "http://127.0.0.1:5001/break-task"
    
    request_data = {
        "task": task,
        "model": model,
        "temperature": 0.3,
        "max_retries": max_retries,
    }
    
    print(f"\n📤 Sending request to service...")
    print(f"Task: {task[:60]}...")
    print(f"Model: {model}")
    print(f"Max retries: {max_retries}\n")
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(request_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            if result.get("status") == "success":
                print("✅ Task breaking succeeded!\n")
                print(f"Tasks identified: {result['task_count']}")
                print(f"Total estimated time: {result['total_estimated_hours']:.1f} hours\n")
                
                print("Task List:")
                print("-" * 80)
                for i, task in enumerate(result["tasks"], 1):
                    diff_bar = "🔴" * task["difficulty"] + "⚪" * (5 - task["difficulty"])
                    print(f"\n{i}. {task['title']}")
                    print(f"   Difficulty: {diff_bar} ({task['difficulty']}/5)")
                    print(f"   Time: {task['estimated_hours']}h")
                    print(f"   {task['description'][:70]}")
                    if task["dependencies"]:
                        deps = ", ".join(task['dependencies'][:2])
                        if len(task['dependencies']) > 2:
                            deps += f", +{len(task['dependencies'])-2} more"
                        print(f"   Dependencies: {deps}")
                
                return True
            else:
                print(f"❌ Error: {result.get('error')}")
                if "details" in result:
                    print(f"Details: {result['details']}")
                return False
    
    except urllib.error.URLError as e:
        print(f"❌ Failed to connect to service: {e}")
        print("\n💡 Make sure the service is running:")
        print("   python3 ollama_orchestrator/tools/task_breaker_service.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_health():
    """Check service health"""
    url = "http://127.0.0.1:5001/health"
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"✅ Service is healthy: {result}")
            return True
    except:
        print("❌ Service is not running")
        return False


def main():
    print("\n" + "=" * 80)
    print("TASK BREAKER SERVICE TEST")
    print("=" * 80)
    
    # Check health
    print("\n1️⃣  Checking service health...")
    if not test_health():
        print("\n💡 Start the service with:")
        print("   python3 ollama_orchestrator/tools/task_breaker_service.py")
        sys.exit(1)
    
    # Test 1: Simple task
    print("\n" + "=" * 80)
    print("2️⃣  Test 1: Simple Task Breakdown")
    print("=" * 80)
    test_service("Build a calculator app")
    
    # Test 2: Complex project
    print("\n" + "=" * 80)
    print("3️⃣  Test 2: Complex Project")
    print("=" * 80)
    test_service(
        """Build a social media platform with:
        - User profiles
        - Friend connections
        - Feed with posts
        - Real-time notifications
        - Search functionality"""
    )
    
    # Test 3: With custom retry count
    print("\n" + "=" * 80)
    print("4️⃣  Test 3: High Retry Count (5)")
    print("=" * 80)
    test_service(
        "Implement machine learning model training pipeline",
        max_retries=5
    )


if __name__ == "__main__":
    main()
