# Ollama Orchestrator

Python module for orchestrating local Ollama models. Provides a REST + CLI wrapper with auto model detection, task decomposition, per-task token measurement, and multi-agent discussion.

Requirements:
- Python 3.9+
- Ollama installed and running with at least one generative model (`ollama pull mistral:7b`)

---

## Orchestrator

Sends a prompt to a local model and returns the response. Supports JSON mode, temperature, and automatic model selection.

```bash
# From the project root
python3 src/ollama_orchestrator/orchestrator.py --prompt "Explain async/await in Python"
python3 src/ollama_orchestrator/orchestrator.py --prompt "..." --model-size smallest
python3 src/ollama_orchestrator/orchestrator.py --prompt "..." --json
```

---

## Task Breaker

Decomposes a project description into numbered subtasks with difficulty ratings, hour estimates, and dependency links. Uses the Ollama REST API (`POST /api/generate`) for token counting; falls back to the CLI if the daemon is unreachable.

```bash
python3 src/ollama_orchestrator/task_breaker.py --prompt "Build a REST API with authentication"
python3 src/ollama_orchestrator/task_breaker.py --prompt "..." --model-size largest --json
```

| Flag | Default | Description |
|---|---|---|
| `--prompt` | required | Project description |
| `--model` | auto | Explicit model name |
| `--model-size` | `largest` | `smallest` or `largest` auto-detected model |
| `--temperature` | `0.3` | LLM temperature |
| `--max-retries` | `3` | Retries on parse failure |
| `--json` | off | JSON output |

See [TASK_BREAKER_README.md](TASK_BREAKER_README.md) for the full Python API, HTTP service reference, and data models.

---

## Tool demo — `orchestrator_with_tools.py`

The orchestrator supports plain-text tool calls. When the model emits `CALL tool_name key=val`, the orchestrator executes the tool and feeds the result back until the model returns a final response.

Start the discussion-length service in one terminal:

```bash
python3 src/ollama_orchestrator/tools/discussion_length_service.py
```

Run the tool demo in another:

```bash
python3 src/ollama_orchestrator/examples/orchestrator_with_tools.py \
  --model qwen2.5:3b --prompt "Calculate 12*(3+4)"
```

---

## Discussion demo — `orchestrator_discussion.py`

Two models debate a topic; a third judges the winner. Each agent can query the discussion-length tool to see how many turns remain.

```bash
# Terminal 1
python3 src/ollama_orchestrator/tools/discussion_length_service.py

# Terminal 2
python3 src/ollama_orchestrator/examples/orchestrator_discussion.py \
  --topic "Should cities prioritize public transit over roads?" \
  --rounds 3 \
  --modelA qwen2.5:3b --modelB qwen2.5:3b --judge qwen2.5:3b
```

Omit `--modelA/B/--judge` to fall back to `OLLAMA_MODEL` env var or `qwen2.5:3b`.
