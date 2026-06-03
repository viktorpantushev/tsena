# Tsena — src/

For installation and quick start see the [root README](../README.md).

---

## Running the expense estimator

```bash
python3 src/tools/expense_estimator.py
```

Enter a budget in USD when prompted. The estimator breaks the project into subtasks, measures real token usage via a local model, and recommends the best cloud model tier.

---

## Core module: `ollama_orchestrator/task_breaker.py`

```python
from ollama_orchestrator.task_breaker import break_down_task, format_task_breakdown

breakdown = break_down_task("Build a REST API", model="qwen2.5:3b")
print(format_task_breakdown(breakdown))
# breakdown.tasks                → list of Task objects
# breakdown.total_estimated_hours → sum of all estimated hours
```

CLI:

```bash
python3 src/ollama_orchestrator/task_breaker.py --prompt "Build a REST API"
python3 src/ollama_orchestrator/task_breaker.py --prompt "Build a REST API" --json
```

---

## HTTP microservice — task_breaker_service (port 5001)

```bash
python3 src/ollama_orchestrator/tools/task_breaker_service.py
```

```bash
curl -X POST http://127.0.0.1:5001/break-task \
  -H "Content-Type: application/json" \
  -d '{"task": "Build a web app", "model": "qwen2.5:3b"}'

curl http://127.0.0.1:5001/health
```

---

## Tests

```bash
jupyter notebook src/test/tsena_demo.ipynb
```

Run cells top-to-bottom. Sections 1–2 need no Ollama; sections 3–9 require Ollama with at least one generative model.

---

## Examples

```bash
python3 src/ollama_orchestrator/examples/task_breaker_demo.py
python3 src/ollama_orchestrator/examples/orchestrator_with_task_breaker.py
python3 src/ollama_orchestrator/examples/orchestrator_discussion.py
```
