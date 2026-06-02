# Tsena

**Cost-effective LLM orchestration for coding** - Save time and tokens!

## Quick Start

All code is in the **[src/](./src/)** directory. Start there!

```bash
cd src/
python3 "expense calculator/expense_calculator.py"
```

## What is Tsena?

Tsena is an LLM orchestration library that:
- 🚀 Breaks down complex tasks into manageable subtasks
- 💰 Manages token budgets intelligently
- 🔄 Switches between small and large models dynamically
- 🗣️ Fixes LLM hallucinations through discussion
- 📊 Provides difficulty ratings and time estimates

## Key Features

- **Task Breaker** - Automatic task decomposition with difficulty and time estimates
- **LLM Orchestration** - Coordinate multiple models while staying in budget
- **Budget Planning** - Monitor and manage token usage
- **Discussion Framework** - Resolve hallucinations through structured dialogue

## Project Structure

```
tsena/
├── LICENSE
├── README.md (this file)
└── src/ ← ALL CODE HERE
    ├── README.md (complete documentation)
    ├── ollama_orchestrator/ (framework & core)
    ├── tools/ (shared services)
    ├── expense calculator/ (project)
    ├── expense estimator/ (project)
    └── test files & docs
```

## See Also

- **[src/README.md](./src/README.md)** - Full documentation and getting started guide
- **[src/TRY_IT.md](./src/TRY_IT.md)** - Quick start commands
- **[src/PLAIN_LANGUAGE_MIGRATION.md](./src/PLAIN_LANGUAGE_MIGRATION.md)** - Technical details

## License

See LICENSE file.