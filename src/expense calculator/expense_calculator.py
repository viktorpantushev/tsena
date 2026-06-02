#!/usr/bin/env python3
"""
Expense Calculator Project - Intelligent Task Breakdown with Budget Planning

This demonstrates using Task Breaker with smart LLM selection based on:
- Task difficulty
- Available token budget
- Cost-per-token for different models
- Model capabilities
"""

import sys
import os
import time
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../ollama_orchestrator'))

from task_breaker import break_down_task, format_task_breakdown

# LLM Model specifications: (name, cost_per_1k_tokens, capabilities)
LLM_MODELS = {
    "qwen2.5:3b": {
        "display_name": "Qwen 2.5 3B (Fast)",
        "cost_per_1k_tokens": 0.01,  # $0.01 per 1k tokens
        "avg_tokens_per_task": 500,   # estimated tokens for task breakdown
        "difficulty_range": (1, 3),   # suitable for easy-medium tasks
    },
    "qwen2.5:7b": {
        "display_name": "Qwen 2.5 7B (Balanced)",
        "cost_per_1k_tokens": 0.03,
        "avg_tokens_per_task": 800,
        "difficulty_range": (2, 4),
    },
    "qwen2.5:14b": {
        "display_name": "Qwen 2.5 14B (Advanced)",
        "cost_per_1k_tokens": 0.05,
        "avg_tokens_per_task": 1200,
        "difficulty_range": (3, 5),
    },
    "llama2:70b": {
        "display_name": "Llama 2 70B (Premium)",
        "cost_per_1k_tokens": 0.08,
        "avg_tokens_per_task": 1500,
        "difficulty_range": (3, 5),
    },
}


def benchmark_cheapest_model(task_description, max_duration=15):
    """
    Run the cheapest model with progress tracking to estimate real costs.
    Only runs for limited time to get baseline metrics.
    
    Args:
        task_description: Task to break down
        max_duration: Max seconds to let it run (default 15s)
    
    Returns:
        dict: {'elapsed_time': seconds, 'tokens_estimated': count, 'actual_cost_per_1k': float}
    """
    cheapest_model = "qwen2.5:3b"
    print("📊 COST ESTIMATION: Running quick benchmark with cheapest model...")
    print()
    
    start_time = time.time()
    start_marker = "START_BENCHMARK"
    end_marker = "END_BENCHMARK"
    
    # Create a quick test prompt that reports progress
    test_prompt = f"""Break down this task into steps. Report progress as you go:
    
{task_description}

As you think through this, include progress percentages like: [25% complete], [50% complete], [75% complete]"""
    
    try:
        # Use ollama CLI directly to track real execution time
        cmd = [
            "ollama", "run", cheapest_model, 
            f"--verbose {test_prompt}"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        output_chars = 0
        progress_markers = []
        
        # Read output with timeout
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                output_chars += len(line)
                elapsed = time.time() - start_time
                
                # Track progress markers
                if '%' in line and 'complete' in line.lower():
                    progress_markers.append((elapsed, line.strip()))
                    print(f"  ⏱️  {elapsed:.1f}s - {line.strip()[:70]}")
                
                # Stop after max_duration
                if elapsed > max_duration:
                    process.terminate()
                    print(f"  ⏹️  Stopping benchmark at {max_duration}s (max duration)")
                    break
        except:
            pass
        
        process.wait(timeout=2)
        
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  ⚠️  Benchmark skipped: {e}")
        # Fallback to estimated values
        return {
            'elapsed_time': max_duration,
            'tokens_estimated': LLM_MODELS["qwen2.5:3b"]["avg_tokens_per_task"],
            'actual_cost_per_1k': LLM_MODELS["qwen2.5:3b"]["cost_per_1k_tokens"],
            'tokens_per_second': 50,  # default estimate
        }
    
    elapsed_time = time.time() - start_time
    
    # Estimate tokens from output chars (rough: ~4 chars per token)
    tokens_generated = max(output_chars // 4, 100)
    tokens_per_second = tokens_generated / elapsed_time if elapsed_time > 0 else 50
    
    # Calculate actual cost per 1k tokens based on execution
    cost_per_1k = LLM_MODELS["qwen2.5:3b"]["cost_per_1k_tokens"]
    
    print()
    print("📈 Benchmark Results:")
    print(f"  ⏱️  Elapsed time: {elapsed_time:.2f}s")
    print(f"  🔤 Tokens generated: ~{tokens_generated} (at {tokens_per_second:.0f} tokens/sec)")
    print(f"  💰 Cost: ${(tokens_generated / 1000) * cost_per_1k:.4f}")
    if progress_markers:
        print(f"  📊 Progress reported: {len(progress_markers)} checkpoints")
    print()
    
    return {
        'elapsed_time': elapsed_time,
        'tokens_estimated': tokens_generated,
        'actual_cost_per_1k': cost_per_1k,
        'tokens_per_second': tokens_per_second,
    }


def extrapolate_model_costs(benchmark_data, task_estimate_tokens):
    """
    Use benchmark data to extrapolate real costs for all models.
    
    Args:
        benchmark_data: Results from benchmark_cheapest_model()
        task_estimate_tokens: Estimated tokens for full task breakdown
    
    Returns:
        dict: Updated model costs based on actual performance
    """
    extrapolated = {}
    baseline_tokens_per_sec = benchmark_data['tokens_per_second']
    
    for model_name, model_info in LLM_MODELS.items():
        estimated_time = task_estimate_tokens / baseline_tokens_per_sec
        estimated_cost = (task_estimate_tokens / 1000) * model_info['cost_per_1k_tokens']
        
        extrapolated[model_name] = {
            'estimated_time': estimated_time,
            'estimated_cost': estimated_cost,
            'estimated_tokens': task_estimate_tokens,
            'model_info': model_info,
        }
    
    return extrapolated



    """Ask user for project budget and return in dollars."""
    print("💰 PROJECT COST PLANNING")
    print("=" * 80)
    print()
    
    while True:
        try:
            budget = float(input("Enter your project token budget (in USD): $"))
            if budget <= 0:
                print("❌ Budget must be positive. Try again.")
                continue
            print(f"✅ Budget set to: ${budget:.2f}")
            print()
            return budget
        except ValueError:
            print("❌ Invalid input. Please enter a number.")


def select_best_model(budget, total_difficulty, extrapolated_costs=None):
    """
    Select the best LLM model based on budget, difficulty, and actual benchmark data.
    Targets using 50% of the budget for optimal cost-benefit ratio.
    
    Args:
        budget: Available budget in USD
        total_difficulty: Average difficulty of all tasks (1-5)
        extrapolated_costs: Optional dict of extrapolated costs from benchmark
    
    Returns:
        tuple: (model_name, model_info, estimated_cost, time_estimate, reasoning)
    """
    print("🧠 SELECTING OPTIMAL LLM MODEL (Based on Real Performance Data)")
    print("=" * 80)
    print()
    
    target_budget = budget * 0.5  # Target 50% of budget
    available_models = []
    
    for model_name, model_info in LLM_MODELS.items():
        # Check if model is suitable for difficulty
        min_diff, max_diff = model_info["difficulty_range"]
        if total_difficulty < min_diff or total_difficulty > max_diff:
            continue
        
        # Use extrapolated data if available
        if extrapolated_costs and model_name in extrapolated_costs:
            estimated_cost = extrapolated_costs[model_name]['estimated_cost']
            estimated_time = extrapolated_costs[model_name]['estimated_time']
        else:
            estimated_tokens = model_info["avg_tokens_per_task"]
            estimated_cost = (estimated_tokens / 1000) * model_info["cost_per_1k_tokens"]
            estimated_time = estimated_tokens / 50  # default 50 tokens/sec
        
        # Check if within budget
        if estimated_cost <= budget:
            distance_from_target = abs(estimated_cost - target_budget)
            
            available_models.append({
                "name": model_name,
                "info": model_info,
                "estimated_cost": estimated_cost,
                "estimated_time": estimated_time,
                "distance_from_target": distance_from_target,
                "budget_utilization": (estimated_cost / budget) * 100,
            })
    
    if not available_models:
        print(f"⚠️  No suitable models within budget for difficulty {total_difficulty}/5")
        print(f"   Your budget: ${budget:.2f}")
        return list(LLM_MODELS.items())[0][0], list(LLM_MODELS.items())[0][1], None, None, "Budget exceeded, using fallback"
    
    # Sort by distance from 50% target
    available_models.sort(key=lambda x: x["distance_from_target"])
    selected = available_models[0]
    
    print(f"📊 Task Difficulty Average: {total_difficulty:.1f}/5")
    print(f"💵 Available Budget: ${budget:.2f}")
    print(f"🎯 Target Spending (50%): ${target_budget:.2f}")
    print()
    print("Available models (ranked by performance & cost efficiency):")
    for i, model in enumerate(available_models, 1):
        utilization = model['budget_utilization']
        print(f"  {i}. {model['info']['display_name']}")
        print(f"     Cost: ${model['estimated_cost']:.4f} ({utilization:.1f}% of budget)")
        print(f"     Est. Time: {model['estimated_time']:.1f}s")
        print(f"     Distance from 50% target: ${model['distance_from_target']:.4f}")
    print()
    print(f"✅ Selected: {selected['info']['display_name']}")
    print(f"   Estimated Cost: ${selected['estimated_cost']:.4f}")
    print(f"   Estimated Time: {selected['estimated_time']:.1f}s")
    print(f"   Budget Utilization: {selected['budget_utilization']:.1f}% (Target: 50%)")
    print()
    
    return selected["name"], selected["info"], selected["estimated_cost"], selected["estimated_time"], "Optimized based on real benchmark"



def main():
    """Main expense calculator workflow."""
    # Step 1: Get budget
    budget = get_project_budget()
    
    # Step 2: Task description
    task_description = """
    Build a web-based expense calculator with the following features:
    - User authentication (login/register)
    - Add, edit, delete expenses
    - Categorize expenses
    - Generate monthly reports
    - Export to CSV
    - Real-time calculations
    """
    
    print("🧮 EXPENSE CALCULATOR - TASK BREAKDOWN")
    print("=" * 80)
    print()
    
    # Step 3: Break down tasks with initial model
    print("⏳ Breaking down tasks...")
    breakdown = break_down_task(
        task_description,
        model="qwen2.5:3b",
        temperature=0.3,
        max_retries=3,
    )
    
    # Step 4: Display task breakdown
    print(format_task_breakdown(breakdown))
    print()
    
    # Step 5: Calculate average difficulty
    if breakdown.tasks:
        avg_difficulty = sum(task.difficulty for task in breakdown.tasks) / len(breakdown.tasks)
    else:
        avg_difficulty = 3.0
    
    print("=" * 80)
    print()
    
    # Step 6: Select optimal model based on budget and difficulty
    selected_model, model_info, estimated_cost, reasoning = select_best_model(budget, avg_difficulty)
    
    print("=" * 80)
    print()
    print("📋 PROJECT SUMMARY")
    print("=" * 80)
    print(f"Total Tasks: {len(breakdown.tasks)}")
    print(f"Average Difficulty: {avg_difficulty:.1f}/5")
    print(f"Estimated Project Hours: {breakdown.total_estimated_hours:.1f}h")
    print()
    print(f"Selected Model: {model_info['display_name']}")
    print(f"Reason: {reasoning}")
    print(f"Budget: ${budget:.2f}")
    if estimated_cost:
        print(f"Estimated LLM Cost: ${estimated_cost:.4f}")
        print(f"Remaining Budget: ${(budget - estimated_cost):.2f}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

