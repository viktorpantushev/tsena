# Task Breaker

Decomposes a project description into subtasks using a local LLM. Each task gets a difficulty rating (1–5), an hour estimate, and a dependency list. Responses are plain-language numbered lists — no JSON from the model — parsed with a flexible regex-based extractor.

---

## Usage

### CLI

```bash
python3 src/ollama_orchestrator/task_breaker.py \
  --prompt "Build a real-time chat application with user authentication"
```

Output:

```
Task Breakdown: Build a real-time chat application with user authentication
Total Estimated Hours: 45.5
--------------------------------------------------------------------------------

1. Set up project structure and dependencies
   Difficulty: 🔴⚪⚪⚪⚪ (1/5)
   Estimated: 1.5 hours
   Description: Create project directory, initialize package manager, install dependencies

2. Implement user authentication system
   Difficulty: 🔴🔴🔴⚪⚪ (3/5)
   Estimated: 8.0 hours
   ...
```

JSON output:

```bash
python3 src/ollama_orchestrator/task_breaker.py --prompt "Build a REST API" --json
```

### Python API

```python
from ollama_orchestrator.task_breaker import break_down_task, format_task_breakdown

breakdown = break_down_task(
    "Build a web application",
    model="mistral:7b",       # optional — defaults to auto-detected largest
    temperature=0.3,
    max_retries=3,
)

print(format_task_breakdown(breakdown))

for task in breakdown.tasks:
    print(f"{task.title}: difficulty {task.difficulty}/5, {task.estimated_hours}h")
    print(f"  deps: {task.dependencies}")

print(f"Total: {breakdown.total_estimated_hours:.1f}h")
```

---

## HTTP service (port 5001)

```bash
python3 src/ollama_orchestrator/tools/task_breaker_service.py
```

#### POST /break-task

```bash
curl -X POST http://127.0.0.1:5001/break-task \
  -H "Content-Type: application/json" \
  -d '{"task": "Build a web application", "model": "qwen2.5:3b", "max_retries": 3}'
```

Response:

```json
{
  "status": "success",
  "original_prompt": "Build a web application",
  "total_estimated_hours": 45.5,
  "task_count": 8,
  "tasks": [
    {
      "title": "Set up project structure",
      "description": "Create directory layout and install dependencies",
      "difficulty": 1,
      "estimated_hours": 1.5,
      "dependencies": []
    }
  ]
}
```

#### GET /health

```json
{"status": "healthy", "service": "task-breaker"}
```

---

## Data models

```python
@dataclass
class Task:
    title: str
    description: str
    difficulty: int          # 1–5
    estimated_hours: float
    dependencies: list[str]  # task titles this depends on

@dataclass
class TaskBreakdown:
    original_prompt: str
    tasks: list[Task]
    total_estimated_hours: float
```

---

## Retry logic

On parse failure the task breaker retries up to `max_retries` times. Each retry:
- Makes the prompt more explicit (stricter formatting instructions, inline example)
- Raises temperature by 0.1 to encourage variation

Default: 3 attempts. Override with `--max-retries` (CLI) or the `max_retries` parameter (Python/HTTP).

---

## Plain-language parser

The LLM is prompted to respond in this format:

```
1. Task Title
Description of what needs to be done.
Difficulty: 3
Estimated: 4 hours
Depends on: Other Task
```

The parser accepts numbered lists, dash lists (`- Title`), and bullet points (`• Title`). Missing metadata fields fall back to difficulty 3, 2.0 hours, and no dependencies.

---

## Difficulty scale

| Level | Label | Meaning |
|---|---|---|
| 1 | Trivial | Straightforward, well-documented |
| 2 | Easy | Standard implementation, good patterns available |
| 3 | Medium | Some complexity, requires planning |
| 4 | Hard | Complex logic, significant design decisions |
| 5 | Very Hard | Cutting-edge, unclear requirements |

---

## Model recommendations

| Size | Model | Notes |
|---|---|---|
| Small/fast | `qwen2.5:3b` | Quick decomposition, may need more retries |
| Balanced | `mistral:7b` | Follows format reliably, recommended minimum |
| Large | `llama2:13b`+ | Best task understanding for complex projects |

---

## Troubleshooting

**Service connection refused** — start the service first: `python3 src/ollama_orchestrator/tools/task_breaker_service.py`

**No tasks parsed** — use a larger model (`--model-size largest` or `--model mistral:7b`) and increase retries (`--max-retries 5`). Sub-3B models often ignore formatting instructions.

**Model not found** — `ollama pull <model-name>` first.

---

## Testing

Run the interactive test suite:

```bash
jupyter notebook src/test/tsena_demo.ipynb
```

Sections 1–2 cover parser unit tests (no Ollama needed). Sections 3–9 test the full pipeline and HTTP service (requires Ollama).
