# Ollama Orchestrator (Python)

Minimal example showing how to orchestrate local Ollama models from Python
using the `ollama` CLI.

Requirements
- `ollama` installed and running locally; model(s) available via Ollama.
- Python 3.8+

Usage

Run the orchestrator from the repo root:

```bash
python3 ollama_orchestrator/orchestrator.py --model <model> --prompt "Hello world"
```

Request JSON output (if the CLI supports `--json`):

```bash
python3 ollama_orchestrator/orchestrator.py --model <model> --prompt "Hello" --json
```

Notes
- This implementation uses the `ollama` CLI via `subprocess`. If you prefer
  an HTTP API (if available in your environment), adapt the script to use
  `requests` or an async HTTP client.
- CLI flags such as `--temperature`, `--max-tokens`, and `--json` are passed
  through when supported by your `ollama` installation.

Tool demo

1. Start the discussion-length tool in a terminal:

```bash
python3 ollama_orchestrator/tools/discussion_length_service.py
```

2. In another terminal run the orchestrator that demonstrates LLM tool calls.

You can pass the model explicitly:

```bash
python3 ollama_orchestrator/examples/orchestrator_with_tools.py --model qwen2.5:3b --prompt "Calculate 12*(3+4)"
```

Or set the `OLLAMA_MODEL` environment variable (defaults to `quen3.5`):

```bash
export OLLAMA_MODEL=qwen2.5:3b
python3 ollama_orchestrator/examples/orchestrator_with_tools.py --prompt "Calculate 12*(3+4)"
```

The orchestrator instructs the model to use a plain-text tool call when it wants
to call the `discussion_length` tool, for example:
`CALL discussion_length current_turn=2 max_turns=6`.
The orchestrator executes the tool and feeds the result back to the model until
the result back to the model until the model returns a final JSON response.

Discussion demo

Agents can now ask the discussion-length tool how many turns are left during the debate.

Start the tool service in one terminal:

```bash
python3 ollama_orchestrator/tools/discussion_length_service.py
```

Run the debate orchestrator in another terminal:

```bash
python3 ollama_orchestrator/examples/orchestrator_discussion.py \
  --topic "Should cities prioritize public transit over roads?" \
  --rounds 3 \
  --modelA qwen2.5:3b --modelB qwen2.5:3b --judge qwen2.5:3b
```

You can omit `--modelA`, `--modelB`, and `--judge` to use `OLLAMA_MODEL` or the default `qwen2.5:3b`.
