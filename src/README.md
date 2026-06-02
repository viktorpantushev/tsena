# Tsena - Cost-Effective LLM Orchestration for Coding

**Tsena** is an LLM orchestration library all about saving you **time** and **tokens**.

## The Problem
Scared from the LLM token bill? Tsena is here to help!

## The Solution
Using budget planning and smart model switching:
- Use small, fast models for speed
- Use large LLMs for quality results
- Stay within your token budget
- Fix hallucinations with LLM discussions
- No sacrifice of capabilities

## How It Works
With similar properties to a wizard, tsena changes model sizes for:
- Quick code reviews
- Well-documented feature discussions with security analysis
- Documentation and pseudo code generation for speed and clarity

## Directory Structure

```
src/
├── README.md                           (this file)
├── test_*.py                           (test suite)
├── TRY_IT.md                           (quick start guide)
├── PLAIN_LANGUAGE_MIGRATION.md         (technical details)
│
├── ollama_orchestrator/                (framework & core)
│   ├── orchestrator.py
│   ├── task_breaker.py
│   ├── examples/
│   ├── tools/
│   └── README.md
│
├── tools/                              (shared services)
│   ├── task_breaker_service.py
│   ├── discussion_length_service.py
│
├── expense calculator/                 (project 1)
│   └── expense_calculator.py
│
└── expense estimator/                  (project 2)
    └── expense_estimator.py
```

## Projects

### Expense Calculator
A web-based application for tracking and managing personal expenses.

**Features:**
- User authentication
- Add, edit, delete expenses
- Categorize expenses  
- Monthly reports
- CSV export
- Real-time calculations

**Run:**
```bash
python3 expense\ calculator/expense_calculator.py
```

### Expense Estimator
Intelligent ML application for predicting expenses and budgeting.

**Features:**
- Historical analysis
- ML-based prediction
- Budget recommendations
- Overspending alerts
- Multi-currency support
- Recurring expense detection

**Run:**
```bash
python3 expense\ estimator/expense_estimator.py
```

## Shared Tools

### task_breaker_service.py
HTTP microservice for task decomposition.

**Start:**
```bash
python3 tools/task_breaker_service.py
```

**Use:**
```bash
curl -X POST http://127.0.0.1:5001/break-task \
  -H "Content-Type: application/json" \
  -d '{"task": "Build a web app", "model": "qwen2.5:3b"}'
```

### discussion_length_service.py
Tool service for LLM discussion analysis.

## Core Features

### ✅ Task Breaker
Automatically decomposes complex tasks into subtasks with:
- Difficulty ratings (1-5)
- Time estimates
- Dependency tracking
- Plain language processing
- Automatic retry logic

### ✅ LLM Discussion
Structured discussions to fix hallucinations

### ✅ Budget Planning
Intelligent token budget management

### ✅ Orchestration
Multi-model coordination

## Quick Start

### 1. Try a breakdown:
```bash
python3 expense\ calculator/expense_calculator.py
```

### 2. Start services:
```bash
python3 tools/task_breaker_service.py
```

### 3. Run tests:
```bash
python3 test_task_breaker.py
python3 test_plain_language_parser.py
python3 test_service.py
```

## Documentation

- **[TRY_IT.md](./TRY_IT.md)** - All ways to try Task Breaker
- **[PLAIN_LANGUAGE_MIGRATION.md](./PLAIN_LANGUAGE_MIGRATION.md)** - JSON to plain language migration details

## License

See LICENSE in the project root.
