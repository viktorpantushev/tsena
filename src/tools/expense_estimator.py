#!/usr/bin/env python3
"""
Expense Estimator Project - Intelligent Task Breakdown with Budget Planning

An advanced application demonstrating:
- Task breakdown for ML-based expense prediction
- Budget-aware LLM selection
- Difficulty-based model recommendation
- Cost optimization for complex projects
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../ollama_orchestrator'))

from task_breaker import (
    break_down_task,
    format_task_breakdown,
    get_largest_generative_model,
    measure_tasks,
)

# LLM Model specifications: (name, cost_per_1k_tokens, capabilities)
LLM_MODELS = {
    "qwen2.5:3b": {
        "display_name": "Qwen 2.5 3B (Fast)",
        "cost_per_1k_tokens": 0.01,
        "avg_tokens_per_task": 500,
        "difficulty_range": (1, 3),
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
        "display_name": "Llama 2 70B (Premium - ML Ready)",
        "cost_per_1k_tokens": 0.08,
        "avg_tokens_per_task": 1500,
        "difficulty_range": (3, 5),
    },
}


def get_project_budget():
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


def choose_model() -> str:
    """List available generative models and ask the user to pick one by name or number."""
    import subprocess as _sp

    print("MODEL SELECTION")
    print("=" * 80)

    # Collect available generative models (deduplicated by ID)
    models: list[str] = []
    try:
        proc = _sp.run(["ollama", "list"], capture_output=True, text=True)
        seen_ids: set[str] = set()
        for line in proc.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            name, model_id = parts[0], parts[1]
            if "embed" in name.lower():
                continue
            if model_id in seen_ids:
                continue
            seen_ids.add(model_id)
            models.append(name)
    except Exception:
        pass

    if models:
        print("Available models:")
        for i, name in enumerate(models, 1):
            print(f"  {i}. {name}")
    else:
        print("  (could not list models)")
    print()

    while True:
        choice = input("Enter model name or number: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                print(f"Using model: {selected}")
                print()
                return selected
            print(f"  Please enter a number between 1 and {len(models)}.")
        elif choice in models:
            print(f"Using model: {choice}")
            print()
            return choice
        elif choice:
            # Accept any name the user types even if not in the list
            print(f"Using model: {choice}")
            print()
            return choice
        else:
            print("  Please enter a model name or number.")


def select_best_model(budget, total_difficulty, actual_tokens_per_task=None):
    """
    Select the best LLM model based on budget and average task difficulty.
    For ML projects, targets 50% budget for more capable models.

    Args:
        budget: Available budget in USD
        total_difficulty: Average difficulty of all tasks (1-5)
        actual_tokens_per_task: Real token count from a measured run (overrides avg_tokens_per_task)

    Returns:
        tuple: (model_name, model_info, estimated_cost, reasoning)
    """
    print("SELECTING OPTIMAL LLM MODEL (ML-Aware, Targeting 50% Budget)")
    print("=" * 80)
    print()

    target_budget = budget * 0.5  # Target 50% of budget
    available_models = []

    for model_name, model_info in LLM_MODELS.items():
        # Check if model is suitable for difficulty
        min_diff, max_diff = model_info["difficulty_range"]
        if total_difficulty < min_diff or total_difficulty > max_diff:
            continue

        # Use actual measured tokens when available, otherwise fall back to estimate
        tokens = actual_tokens_per_task if actual_tokens_per_task else model_info["avg_tokens_per_task"]
        estimated_cost = (tokens / 1000) * model_info["cost_per_1k_tokens"]

        if estimated_cost <= budget:
            distance_from_target = abs(estimated_cost - target_budget)
            capability_weight = 1.0 if total_difficulty <= 3 else 0.5
            score = distance_from_target * capability_weight

            available_models.append({
                "name": model_name,
                "info": model_info,
                "tokens_used": tokens,
                "estimated_cost": estimated_cost,
                "distance_from_target": distance_from_target,
                "budget_utilization": (estimated_cost / budget) * 100,
                "score": score,
            })

    if not available_models:
        print(f"  No suitable models within budget for difficulty {total_difficulty}/5")
        print(f"   Your budget: ${budget:.2f}")
        print(f"   Selecting cheapest model: {list(LLM_MODELS.keys())[0]}")
        return list(LLM_MODELS.items())[0][0], list(LLM_MODELS.items())[0][1], None, "Budget exceeded, using fallback"

    available_models.sort(key=lambda x: x["score"])
    selected = available_models[0]

    token_source = "actual measured" if actual_tokens_per_task else "estimated"
    print(f"  Task Difficulty Average: {total_difficulty:.1f}/5 (ML Project)")
    print(f"  Available Budget: ${budget:.2f}")
    print(f"  Target Spending (50%): ${target_budget:.2f}")
    print(f"  Token count source: {token_source} ({selected['tokens_used']} tokens/task)")
    print()
    print("Available models (sorted by 50% target + ML capability):")
    for i, model in enumerate(available_models, 1):
        utilization = model["budget_utilization"]
        print(f"  {i}. {model['info']['display_name']}")
        print(f"     Cost: ${model['estimated_cost']:.4f} ({utilization:.1f}% of budget)")
        print(f"     Tokens/task: {model['tokens_used']} ({token_source})")
    print()
    print(f"  Selected: {selected['info']['display_name']}")
    print(f"   Estimated Cost: ${selected['estimated_cost']:.4f}")
    print(f"   Budget Utilization: {selected['budget_utilization']:.1f}% (Target: 50%)")
    print()

    return selected["name"], selected["info"], selected["estimated_cost"], f"ML-optimized ~50% budget utilization ({token_source} tokens)"


def main():
    """Main expense estimator workflow."""
    # Step 1: Get budget
    budget = get_project_budget()
    
    # Step 2: Task description
    task_description = """
    Build an intelligent expense estimator application with:
    - Historical expense analysis
    - ML-based prediction of future expenses
    - Budget recommendations
    - Alerts for overspending
    - Multi-currency support
    - Recurring expense detection
    - API for integration with other services
    - Mobile app support
    """
    
    print("💰 EXPENSE ESTIMATOR - TASK BREAKDOWN")
    print("=" * 80)
    print()
    
    # Step 3: Let user pick a model, then break down tasks
    chosen_model = choose_model()
    print(f"Breaking down tasks with model: {chosen_model}")
    print()
    breakdown = break_down_task(
        task_description,
        model=chosen_model,
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

    # Step 6: Run each task through the LLM to measure real per-task token usage
    measurement_model = get_largest_generative_model()
    print("PER-TASK TOKEN MEASUREMENT")
    print("=" * 80)
    print(f"Running each task with {measurement_model} to measure real code-generation tokens...")
    print()
    measure_tasks(breakdown, model=measurement_model)

    # Compute per-task averages from measurements
    if breakdown.measurements:
        total_measured = sum(m.total_tokens for m in breakdown.measurements)
        actual_tokens_per_task = total_measured / len(breakdown.measurements)

        print("=" * 80)
        print("PER-TASK TOKEN BREAKDOWN")
        print("=" * 80)
        for m in breakdown.measurements:
            print(f"  {m.task_title[:60]}")
            print(f"    prompt={m.prompt_tokens}, response={m.response_tokens}, total={m.total_tokens}")
        print(f"\n  Average per task: {actual_tokens_per_task:.0f} tokens")
        print()
    else:
        actual_tokens_per_task = None

    print("=" * 80)
    print()

    # Step 7: Select optimal model based on budget, difficulty, and real token data
    selected_model, model_info, estimated_cost, reasoning = select_best_model(
        budget, avg_difficulty, actual_tokens_per_task=actual_tokens_per_task
    )

    print("=" * 80)
    print()
    print("PROJECT SUMMARY")
    print("=" * 80)
    print(f"Total Tasks:              {len(breakdown.tasks)}")
    print(f"Average Difficulty:       {avg_difficulty:.1f}/5")
    print(f"Estimated Project Hours:  {breakdown.total_estimated_hours:.1f}h")
    if actual_tokens_per_task:
        print(f"Measured Tokens/Task:     {actual_tokens_per_task:.0f} (real code-gen run)")
    print()
    print(f"Recommended Model:  {model_info['display_name']}")
    print(f"Reason:             {reasoning}")
    print(f"Budget:             ${budget:.2f}")
    if estimated_cost:
        print(f"Estimated LLM Cost: ${estimated_cost:.4f}")
        print(f"Remaining Budget:   ${(budget - estimated_cost):.2f}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
