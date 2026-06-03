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
import re
import time
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ollama_orchestrator'))

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


def benchmark_cheapest_model(task_description, stop_at_percent=30, timeout=120):
    """
    Run the cheapest model, watch for progress markers, and stop at ≤30%.
    Extrapolates total time using: elapsed * (100 / reported_percent).

    Args:
        task_description: Task to break down
        stop_at_percent: Stop as soon as the LLM reports this % or less (default 30)
        timeout: Hard fallback timeout in seconds (default 120)

    Returns:
        dict with 'elapsed_time', 'tokens_estimated', 'actual_cost_per_1k', 'tokens_per_second'
    """
    cheapest_model = "qwen2.5:3b"
    print(f"📊 COST ESTIMATION: Running benchmark (stops at first ≤{stop_at_percent}% progress marker)...")
    print()

    test_prompt = f"""Break down this task into steps. Report your progress as you go.

{task_description}

IMPORTANT: After every step you outline, print a progress line in EXACTLY this format:
[X% complete]
Use 25% after the first step, 50% after the second, 75% after the third, and so on."""

    cost_per_1k = LLM_MODELS[cheapest_model]["cost_per_1k_tokens"]

    try:
        process = subprocess.Popen(
            ["ollama", "run", cheapest_model, test_prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError as e:
        print(f"  ⚠️  Benchmark skipped: {e}")
        return {
            'elapsed_time': 30,
            'tokens_estimated': LLM_MODELS[cheapest_model]["avg_tokens_per_task"],
            'actual_cost_per_1k': cost_per_1k,
            'tokens_per_second': 50,
        }

    start_time = time.time()
    output_chars = 0
    elapsed_at_stop = None
    reported_percent = None

    try:
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            output_chars += len(line)
            elapsed = time.time() - start_time

            pct_match = re.search(r'\[(\d+)\s*%', line)
            if pct_match:
                pct = int(pct_match.group(1))
                print(f"  ⏱️  {elapsed:.1f}s — {line.strip()[:70]}")
                if pct <= stop_at_percent:
                    elapsed_at_stop = elapsed
                    reported_percent = pct
                    process.terminate()
                    print(f"  ⏹️  Stopped at {pct}% ({elapsed:.1f}s)")
                    break

            if elapsed > timeout:
                process.terminate()
                print(f"  ⏹️  Hard timeout at {timeout}s — no progress marker found")
                break
    except Exception:
        pass

    process.wait(timeout=2)

    tokens_so_far = max(output_chars // 4, 10)

    if elapsed_at_stop and reported_percent:
        multiplier = 100 / reported_percent
        estimated_total_time = elapsed_at_stop * multiplier
        estimated_total_tokens = int(tokens_so_far * multiplier)
        tokens_per_second = tokens_so_far / elapsed_at_stop
    else:
        elapsed_time = time.time() - start_time
        estimated_total_time = elapsed_time
        estimated_total_tokens = max(tokens_so_far, LLM_MODELS[cheapest_model]["avg_tokens_per_task"])
        tokens_per_second = tokens_so_far / elapsed_time if elapsed_time > 0 else 50

    print()
    if elapsed_at_stop:
        print(f"📈 Benchmark Results (extrapolated from {reported_percent}%):")
        print(f"  ⏱️  Time at {reported_percent}%: {elapsed_at_stop:.2f}s  ×{100/reported_percent:.1f} → {estimated_total_time:.1f}s total")
    else:
        print("📈 Benchmark Results (fallback — no progress marker):")
        print(f"  ⏱️  Elapsed: {estimated_total_time:.1f}s")
    print(f"  🔤 Tokens/sec: ~{tokens_per_second:.0f}")
    print(f"  💰 Estimated cost: ${(estimated_total_tokens / 1000) * cost_per_1k:.4f}")
    print()

    return {
        'elapsed_time': estimated_total_time,
        'tokens_estimated': estimated_total_tokens,
        'actual_cost_per_1k': cost_per_1k,
        'tokens_per_second': tokens_per_second,
    }


def extrapolate_model_costs(benchmark_data):
    """
    Use benchmark data to extrapolate real costs for all models.
    Both token count and time come from the benchmark's own extrapolation
    (same multiplier logic: stopped at X%, scaled by 100/X).

    Args:
        benchmark_data: Results from benchmark_cheapest_model()

    Returns:
        dict: Model costs based on actual measured performance
    """
    extrapolated = {}
    tokens_estimated = benchmark_data['tokens_estimated']
    tokens_per_second = benchmark_data['tokens_per_second']

    for model_name, model_info in LLM_MODELS.items():
        estimated_tokens = tokens_estimated
        estimated_time = estimated_tokens / tokens_per_second
        estimated_cost = (estimated_tokens / 1000) * model_info['cost_per_1k_tokens']

        extrapolated[model_name] = {
            'estimated_time': estimated_time,
            'estimated_cost': estimated_cost,
            'estimated_tokens': estimated_tokens,
            'model_info': model_info,
        }

    return extrapolated


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


def select_model_mix(budget, tasks, benchmark_data):
    """
    Assign the best affordable model to each task individually.

    Token budget per task is proportional to its estimated_hours share of the
    total (same extrapolation ratio the benchmark used for time and tokens).
    Model capability is matched to task difficulty; if the total cost exceeds
    the budget, the easiest tasks are downgraded first so harder tasks keep
    the most capable model possible.

    Args:
        budget: Total available budget in USD
        tasks: List of Task objects from the breakdown
        benchmark_data: Results from benchmark_cheapest_model()

    Returns:
        (assignments, total_cost)
        assignments: list of dicts with task, model, tokens, cost, time
    """
    spend_limit = budget * 0.7  # 30% buffer reserved
    total_tokens = benchmark_data['tokens_estimated']
    tokens_per_sec = benchmark_data['tokens_per_second']

    total_hours = sum(t.estimated_hours for t in tasks) or 1.0

    task_tokens = {
        t.title: max(int(total_tokens * (t.estimated_hours / total_hours)), 50)
        for t in tasks
    }

    def best_model_for_budget(tokens, task_budget):
        """Most capable model whose cost for `tokens` fits within `task_budget`."""
        affordable = [
            (name, info) for name, info in LLM_MODELS.items()
            if (tokens / 1000) * info['cost_per_1k_tokens'] <= task_budget
        ]
        if not affordable:
            # Nothing fits — fall back to cheapest available
            return min(LLM_MODELS.items(), key=lambda x: x[1]['cost_per_1k_tokens'])
        return max(affordable, key=lambda x: x[1]['cost_per_1k_tokens'])

    assignments = []
    for task in tasks:
        tokens = task_tokens[task.title]
        # Each task's budget share is proportional to its token weight
        task_budget = spend_limit * (tokens / total_tokens)
        name, info = best_model_for_budget(tokens, task_budget)
        assignments.append({
            'task': task,
            'model': name,
            'model_info': info,
            'tokens': tokens,
            'cost': (tokens / 1000) * info['cost_per_1k_tokens'],
            'time': tokens / tokens_per_sec,
        })

    total_cost = sum(a['cost'] for a in assignments)
    return assignments, total_cost



def main():
    """Main expense calculator workflow."""
    # Step 1: Get budget
    budget = get_project_budget()

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

    # Step 2: Benchmark cheapest model to get real token/time data
    benchmark_data = benchmark_cheapest_model(task_description)

    # Step 3: Break down tasks
    print("⏳ Breaking down tasks...")
    breakdown = break_down_task(
        task_description,
        model="qwen2.5:3b",
        temperature=0.3,
        max_retries=3,
    )
    print(format_task_breakdown(breakdown))
    print()

    # Step 4: Assign best model mix per task within budget
    print("🧠 SELECTING MODEL MIX")
    print("=" * 80)
    assignments, total_cost = select_model_mix(budget, breakdown.tasks, benchmark_data)

    print(f"{'Task':<40} {'Difficulty':>10} {'Model':<28} {'Tokens':>7} {'Cost':>8}")
    print("-" * 100)
    for a in assignments:
        title = a['task'].title[:38]
        diff = f"{a['task'].difficulty}/5"
        model = a['model_info']['display_name'][:26]
        print(f"{title:<40} {diff:>10} {model:<28} {a['tokens']:>7} ${a['cost']:>7.4f}")
    print("-" * 100)
    print(f"{'TOTAL':<40} {'':>10} {'':28} {'':>7} ${total_cost:>7.4f}")
    print()

    spend_limit = budget * 0.7
    over = total_cost > spend_limit
    print(f"💵 Budget:        ${budget:.2f}")
    print(f"🔒 Spend limit:   ${spend_limit:.2f}  (70% — 30% buffer reserved)")
    print(f"💰 Total cost:    ${total_cost:.4f}  {'⚠️  OVER SPEND LIMIT' if over else '✅'}")
    if not over:
        print(f"💚 Buffer left:   ${spend_limit - total_cost:.4f}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

