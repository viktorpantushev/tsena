# Tsena — src/

For installation and quick start see the [root README](../README.md).

---

## Running the expense calculator

```bash
cd src
python3 "expense calculator/expense_calculator.py"
```

Enter a budget in USD when prompted. Suggested values to see different model mixes:

| Budget | What you'll see |
|---|---|
| `$0.05` | qwen2.5:3b for most tasks |
| `$0.10` | qwen2.5:14b for most tasks |
| `$1.00` | llama2:70b where available |

---

## Core module: `ollama_orchestrator/task_breaker.py`

```python
from ollama_orchestrator.task_breaker import break_down_task, format_task_breakdown

breakdown = break_down_task("Build a REST API", model="qwen2.5:3b")
print(format_task_breakdown(breakdown))
# breakdown.tasks          → list of Task(title, description, difficulty, estimated_hours, dependencies)
# breakdown.total_estimated_hours → sum of all task hours
```

CLI usage:

```bash
python3 ollama_orchestrator/task_breaker.py --prompt "Build a REST API"
python3 ollama_orchestrator/task_breaker.py --prompt "Build a REST API" --json
```

---

## HTTP microservices

### task_breaker_service — port 5001

```bash
python3 tools/task_breaker_service.py
```

```bash
curl -X POST http://127.0.0.1:5001/break-task \
  -H "Content-Type: application/json" \
  -d '{"task": "Build a web app", "model": "qwen2.5:3b"}'
```

Health check: `curl http://127.0.0.1:5001/health`

---

## Tests

```bash
python3 test_plain_language_parser.py   # no ollama needed
python3 test_task_breaker.py            # requires ollama + qwen2.5:3b
python3 test_service.py                 # requires ollama + qwen2.5:3b
```

---

## Examples

```bash
python3 ollama_orchestrator/examples/task_breaker_demo.py
python3 ollama_orchestrator/examples/orchestrator_with_task_breaker.py
python3 ollama_orchestrator/examples/orchestrator_discussion.py
```
