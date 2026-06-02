# Tsena

**Cost-effective LLM orchestration** — run the right model for each task and stay within budget.

Tsena breaks a project into subtasks, benchmarks a small model to measure real token speed and cost, then assigns the best affordable LLM to each task. Hard tasks get capable models; easy tasks get fast, cheap ones. A 30% cost buffer is reserved automatically.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.9 or newer |
| [Ollama](https://ollama.com/download) | any recent release |

No pip packages are needed. See [requirements.txt](./requirements.txt).

---

## Installation

### 1. Install Ollama

Follow the instructions at https://ollama.com/download for your OS, then verify:

```bash
ollama --version
```

### 2. Pull the required model

```bash
ollama pull qwen2.5:3b
```

Pull optional models to unlock better quality at higher budgets:

```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
ollama pull llama2:70b
```

Tsena picks the most capable model each task can afford, so pulling more models gives it more choices.

### 3. Clone the repository

```bash
git clone https://github.com/your-org/tsena.git
cd tsena
```

No `pip install` step needed.

---

## Quick Start

```bash
cd src
python3 "expense calculator/expense_calculator.py"
```

You will be prompted for a budget in USD (e.g. `0.10` or `1.00`). Tsena will:

1. Run a short benchmark on `qwen2.5:3b`, stop at the first progress marker, and extrapolate total token count and time
2. Break the project into subtasks with difficulty ratings and hour estimates
3. Assign each task the best model its proportional share of the budget can afford
4. Print a per-task model assignment table and remaining budget

---

## Feature status

### Core framework

| Feature | Status | Notes |
|---|---|---|
| Task breakdown (LLM → subtasks with difficulty + hours) | ✅ Done | `task_breaker.py`, plain-language parser, retry logic |
| Benchmark cheapest model to measure real token speed | ✅ Done | Runs `qwen2.5:3b`, extrapolates from elapsed time |
| Stop benchmark at first progress marker (≤30%) | ⚠️ Partial | Small models often ignore `[X% complete]` format; falls back to full elapsed time |
| Token + time extrapolation from partial benchmark run | ✅ Done | `tokens_so_far × (100 / reported_pct)`, same formula for both |
| Budget-aware model mix (different model per task) | ✅ Done | Per-task budget = `spend_limit × (task_tokens / total_tokens)` |
| 30% cost buffer | ✅ Done | Hard spend limit = 70% of budget |
| Dynamic model selection by token cost, not hardcoded tiers | ✅ Done | Best affordable model per task; easy tasks automatically get smaller models |
| Ollama CLI wrapper (temperature, max-tokens, JSON mode) | ✅ Done | `orchestrator.py` |
| LLM discussion (two models debate, third judges) | ✅ Done | `examples/orchestrator_discussion.py` |
| Tool use via prompt (`CALL tool_name key=val`) | ✅ Done | Used in discussion example |
| HTTP microservice — task breakdown (port 5001) | ✅ Done | `tools/task_breaker_service.py` |
| HTTP microservice — discussion turn counter (port 5000) | ✅ Done | `tools/discussion_length_service.py` |

### Not yet implemented

| Feature | Notes |
|---|---|
| Actually executing the selected model mix | Selection is printed; tasks are not run through their assigned models yet |
| Mid-task model switching | Model is assigned upfront; no runtime switching if a task turns out harder than expected |
| Automatic hallucination detection + discussion trigger | Discussion framework exists but is not wired to the task pipeline |
| Reliable progress marker detection | Depends on small models following instruction format — they often don't |
| Expense tracking UI | The "expense calculator" is an orchestration demo, not a working expense app |
| ML-based expense prediction | Described in `expense_estimator.py`'s task list but not implemented |
| Multi-currency support | Listed as a project feature, not built |
| Recurring expense detection | Listed as a project feature, not built |

---

## How the model selection works

```
Total tokens (extrapolated from benchmark)
  └─ distributed to tasks proportionally by estimated hours
       └─ each task gets: spend_limit × (task_tokens / total_tokens)
            └─ picks the most capable model whose cost ≤ task_budget
```

- **Spend limit** = 70% of your budget (30% buffer always reserved)
- **Easy tasks** (few hours → fewer tokens → smaller budget) → land on smaller models
- **Hard tasks** (many hours → more tokens → larger budget) → can afford better models
- No hardcoded difficulty tiers — the budget drives everything dynamically

---

## Project Structure

```
tsena/
├── requirements.txt          no pip deps; lists ollama models needed
├── README.md                 this file
└── src/
    ├── ollama_orchestrator/
    │   ├── task_breaker.py   core: breaks tasks, parses LLM output
    │   ├── orchestrator.py   multi-model coordination
    │   ├── tools/            HTTP microservices
    │   └── examples/         runnable demos
    ├── expense calculator/
    │   └── expense_calculator.py   main demo — budget-aware model mix
    ├── expense estimator/
    │   └── expense_estimator.py    ML project cost estimator
    ├── tools/                shared HTTP services
    └── test_*.py             test suite
```

---

## Running the tests

```bash
cd src
python3 test_plain_language_parser.py   # parser unit tests (no ollama needed)
python3 test_task_breaker.py            # full breakdown tests (requires ollama)
python3 test_service.py                 # HTTP service tests (requires ollama)
```

---

## Troubleshooting

**`ollama: command not found`**
Ollama is not installed or not on your PATH. Download it from https://ollama.com/download.

**`Error: model 'qwen2.5:3b' not found`**
Run `ollama pull qwen2.5:3b` first.

**`Ollama CLI error`**
Make sure the Ollama background service is running. On macOS/Linux: `ollama serve` in a separate terminal, or check that the Ollama app is open.

**Benchmark never finds a progress marker**
The small model ignored the formatting instruction. The fallback still measures real elapsed time and tokens/sec — results will be slightly less accurate but the rest of the pipeline continues normally.

---

## License

See [LICENSE](./LICENSE).
