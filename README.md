# Tsena

**LLM cost estimator** — break a project into tasks, run each task through a local model to measure real token usage, then project what the project would cost on cloud LLM APIs.

Tsena uses [Ollama](https://ollama.com) to run models locally. It decomposes a project description into subtasks, asks the model to write actual code for each subtask (measuring real token counts via the Ollama REST API), and uses those measurements to recommend the best cloud model tier for the budget.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.9 or newer |
| [Ollama](https://ollama.com/download) | any recent release |

No pip packages needed — uses only the standard library. See [requirements.txt](./requirements.txt).

---

## Installation

### 1. Install Ollama

Follow the instructions at https://ollama.com/download for your OS, then verify:

```bash
ollama --version
```

Make sure the Ollama daemon is running (the desktop app handles this on macOS/Windows; on Linux run `ollama serve` in a separate terminal).

### 2. Pull at least one generative model

A 7B model is the minimum recommended size — smaller models tend to ignore structured formatting instructions:

```bash
ollama pull mistral:7b
```

Optionally pull more to give the estimator a wider selection during per-task runs:

```bash
ollama pull qwen2.5:3b   # fast, small — useful for simple tasks
```

Tsena auto-detects all installed models at startup via `ollama list`.

### 3. Clone the repository

```bash
git clone https://github.com/your-org/tsena.git
cd tsena
```

---

## Quick Start

```bash
cd src/expense\ estimator
python3 expense_estimator.py
```

You will be prompted for:

1. **Budget** — your total token spend limit in USD (e.g. `10`)
2. **Model** — which locally installed model to use for task breakdown and measurement (listed by number)

Tsena then:

1. Breaks the project description into subtasks with difficulty ratings and hour estimates
2. Runs each subtask through the chosen model, asking it to write real implementation code — measuring actual `prompt_tokens` and `response_tokens` via the Ollama REST API
3. Prints a per-task token breakdown and calculates the average tokens per task
4. Recommends the best cloud model tier (from the catalogue in `LLM_MODELS`) whose projected cost fits within the budget

---

## How it works

```
1. Task breakdown (one LLM call)
   └─ project description → list of subtasks with difficulty + hour estimates

2. Per-task measurement (one LLM call per subtask)
   └─ "write the code for this task" → real prompt_tokens + response_tokens
        └─ progress markers [PROGRESS: 1/10 ...] trigger early extrapolation printouts

3. Cost projection
   └─ average measured tokens/task × cost_per_1k_tokens for each model tier
        └─ pick the tier whose cost ≈ 50% of budget and fits task difficulty
```

**Progress markers** — the system prompt instructs the model to print `[PROGRESS: 1/10 — ...]` once it has written ~10% of the implementation, then again at 5/10 and 10/10. When a marker appears in the stream, the estimator prints a projected total token count immediately (before the full response arrives). Larger models (7B+) follow this instruction reliably; smaller models may skip it, but real token counts are always captured at the end of the stream regardless.

**Token counting** — uses the Ollama REST API (`POST /api/generate` with `"stream": true`) rather than the CLI, so `prompt_eval_count` and `eval_count` are available in the final streaming chunk. Falls back to the CLI if the REST API is unreachable.

---

## CLI tools

### Task breaker

```bash
cd src/ollama_orchestrator
python3 task_breaker.py --prompt "Build a REST API with authentication"
```

| Flag | Default | Description |
|---|---|---|
| `--prompt` | required | Project or task description |
| `--model` | auto | Explicit model name — overrides `--model-size` |
| `--model-size` | `largest` | `smallest` or `largest` available generative model |
| `--temperature` | `0.3` | LLM temperature |
| `--max-retries` | `3` | Retries on parse failure |
| `--json` | off | Output as JSON instead of formatted text |

### Orchestrator

```bash
cd src/ollama_orchestrator
python3 orchestrator.py --prompt "Explain async/await in Python"
python3 orchestrator.py --prompt "..." --model-size smallest
python3 orchestrator.py --prompt "..." --json
```

Same `--model` / `--model-size` flags as the task breaker.

---

## Feature status

| Feature | Status |
|---|---|
| Task breakdown — subtasks with difficulty + hour estimates | Done |
| Per-task code-gen runs with real token measurement | Done |
| Token counts via Ollama REST API streaming | Done |
| Progress marker detection + early token extrapolation | Done (models ≥7B follow the format reliably) |
| Auto-detect installed models via `ollama list` | Done |
| Deduplicate aliased models (e.g. `mistral:latest` == `mistral:7b`) | Done |
| Budget-aware model recommendation using real token data | Done |
| `--model-size smallest\|largest` flag for CLI tools | Done |
| Ollama CLI wrapper (temperature, JSON mode) | Done |
| LLM discussion (two models debate, third judges) | Done — `examples/orchestrator_discussion.py` |
| Tool use via prompt (`CALL tool_name key=val`) | Done — used in discussion example |
| HTTP microservice — task breakdown (port 5001) | Done — `tools/task_breaker_service.py` |
| HTTP microservice — discussion turn counter (port 5000) | Done — `tools/discussion_length_service.py` |
| Actually executing the full project using the recommended model | Not yet |
| Mid-task model switching if a task runs over budget | Not yet |
| ML-based expense prediction (the demo project builds this) | Not yet |

---

## Project structure

```
tsena/
├── requirements.txt
├── README.md
└── src/
    ├── ollama_orchestrator/
    │   ├── orchestrator.py         Ollama REST + CLI wrapper, model auto-detection
    │   ├── task_breaker.py         Task decomposition, per-task measurement, token streaming
    │   ├── tools/                  HTTP microservices
    │   └── examples/               Runnable demos (discussion, tool use, task breaker)
    ├── expense estimator/
    │   └── expense_estimator.py    Main entry point — budget input, model pick, full pipeline
    ├── expense calculator/
    │   └── expense_calculator.py   Earlier prototype
    ├── tools/                      Shared HTTP services
    └── test_*.py                   Test suite
```

---

## Running the tests

```bash
cd src
python3 test_plain_language_parser.py   # parser unit tests (no Ollama needed)
python3 test_task_breaker.py            # full breakdown tests (requires Ollama)
python3 test_service.py                 # HTTP service tests (requires Ollama)
```

---

## Troubleshooting

**`ollama: command not found`**
Ollama is not installed or not on your PATH. Download from https://ollama.com/download.

**Model not found**
Run `ollama pull <model-name>` first, e.g. `ollama pull mistral:7b`.

**REST API connection refused**
The Ollama daemon is not running. Start it with `ollama serve` or open the Ollama desktop app. The tools fall back to the CLI automatically but token counts will not be available.

**Progress markers never appear**
The model skipped the formatting instruction. This is common with sub-3B models. Real token counts are still captured at the end of the stream — cost estimates remain accurate, you just lose the early extrapolation printout.

**Tasks parsed incorrectly (metadata lines become task titles)**
Use a larger model (`--model-size largest` or `--model mistral:7b`). Small models often fail to follow the structured output format, causing the parser to misread metadata lines as task titles.

---

## License

See [LICENSE](./LICENSE).
