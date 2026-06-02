# 🚀 Task Breaker - Try It Now!

Here are all the ways to try the Task Breaker feature:

## ⚡ Quickest Start (30 seconds)

```bash
# Simple command - Now with plain language parsing!
python3 ollama_orchestrator/task_breaker.py --prompt "Build a calculator"
```

**NEW**: Task Breaker now uses plain language output instead of JSON - more natural, faster, and more reliable!

## 🧪 Test Scripts (Pick One)

### **NEW: Test the Plain Language Parser**
```bash
python3 test_plain_language_parser.py
```
Tests the new plain language parsing feature with various formats (numbered lists, bullets, etc.)

### 1. **Comprehensive Python Test** (Recommended for first time)
```bash
python3 test_task_breaker.py
```
Runs 4 tests:
- ✅ Simple task breakdown
- ✅ Complex project analysis  
- ✅ JSON output format
- ✅ Custom model handling

### 2. **Command Line Tests** (Try different CLI options)
```bash
bash test_task_breaker.sh
```
Shows:
- Basic breakdown
- JSON output
- Custom retries
- Different temperatures

### 3. **Service Tests** (HTTP API)
```bash
# Terminal 1: Start service
python3 ollama_orchestrator/tools/task_breaker_service.py

# Terminal 2: Run tests
python3 test_service.py
```

## 💻 Code Examples (Copy & Paste)

### Python - Most Basic
```python
from ollama_orchestrator.task_breaker import break_down_task

breakdown = break_down_task("Build a todo app")
for task in breakdown.tasks:
    print(f"• {task.title} ({task.difficulty}/5)")
```

### Python - Formatted Output
```python
from ollama_orchestrator.task_breaker import break_down_task, format_task_breakdown

breakdown = break_down_task("Create a payment system")
print(format_task_breakdown(breakdown))
```

### Python - JSON Export
```python
import json
from ollama_orchestrator.task_breaker import break_down_task

breakdown = break_down_task("Build a chat app")
data = {
    "tasks": [{
        "title": t.title,
        "difficulty": t.difficulty,
        "hours": t.estimated_hours
    } for t in breakdown.tasks]
}
print(json.dumps(data, indent=2))
```

### Python - Analysis
```python
from ollama_orchestrator.task_breaker import break_down_task

breakdown = break_down_task("Full-stack web application")

easy = [t for t in breakdown.tasks if t.difficulty <= 2]
hard = [t for t in breakdown.tasks if t.difficulty >= 4]

print(f"Easy: {len(easy)}, Hard: {len(hard)}")
print(f"Total time: {breakdown.total_estimated_hours:.1f}h")
```

## 🌐 HTTP API Examples

### Start Service
```bash
python3 ollama_orchestrator/tools/task_breaker_service.py
```

### Call from Python
```python
import urllib.request
import json

url = "http://127.0.0.1:5001/break-task"
data = {
    "task": "Build a mobile app",
    "model": "qwen2.5:3b",
    "max_retries": 3
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(req) as response:
    result = json.loads(response.read())
    for task in result["tasks"]:
        print(f"• {task['title']} ({task['difficulty']}/5)")
```

### Call from curl
```bash
curl -X POST http://127.0.0.1:5001/break-task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Build a real-time chat application",
    "model": "qwen2.5:3b",
    "max_retries": 3
  }' | python3 -m json.tool
```

## 📝 All Available Test Files

| File | Purpose | How to Run |
|------|---------|-----------|
| `test_task_breaker.py` | Python test suite | `python3 test_task_breaker.py` |
| `test_service.py` | HTTP service tests | `python3 test_service.py` |
| `test_task_breaker.sh` | CLI command examples | `bash test_task_breaker.sh` |
| `examples_task_breaker.py` | 14 code examples | See file for individual examples |
| `QUICKSTART.py` | Quick reference | `python3 QUICKSTART.py` |

## 🎯 What Each Test Does

### test_task_breaker.py
1. **TEST 1**: Simple task → formatted output
2. **TEST 2**: Complex project → analysis
3. **TEST 3**: JSON export → data format
4. **TEST 4**: Model fallback → robustness

### test_service.py
1. **Health Check**: Is service running?
2. **Simple Task**: Basic breakdown via HTTP
3. **Complex Project**: Multi-requirement task
4. **Retry Test**: 5 retries for robustness

### examples_task_breaker.py
14 copy-paste examples including:
- Basic usage
- Formatted output
- JSON export
- Difficulty analysis
- Finding critical path
- Team estimation
- And more...

## 🛠️ Command Line Options

```bash
# All options
python3 ollama_orchestrator/task_breaker.py \
  --prompt "Your task" \              # Required
  --model "qwen2.5:3b" \             # Optional
  --temperature 0.3 \                # Optional (0-1)
  --max-retries 3 \                  # Optional (1+)
  --json                             # Optional flag
```

## 📊 Output Types

### Formatted Table (default)
```
Task Breakdown: Build a calculator
Total Estimated Hours: 12.5
────────────────────────────────────
1. Design UI
   Difficulty: 🔴🔴⚪⚪⚪ (2/5)
   Estimated: 3.0 hours
   ...
```

### JSON (--json flag)
```json
{
  "original_prompt": "...",
  "total_estimated_hours": 12.5,
  "tasks": [...]
}
```

## ⚙️ Requirements

- Python 3.7+
- Ollama installed (`brew install ollama`)
- Model downloaded: `ollama pull qwen2.5:3b`

## ✅ Quick Checklist

- [ ] Run `test_task_breaker.py` for quick test
- [ ] Try a CLI command: `python3 ollama_orchestrator/task_breaker.py --prompt "Your task"`
- [ ] Try different models if available
- [ ] Review `examples_task_breaker.py` for your use case
- [ ] Start service and test HTTP API

## 🐛 Troubleshooting

**"Module not found"**
```bash
cd /Users/viktor/PycharmProjects/tsena
```

**"Ollama not found"**
```bash
brew install ollama
ollama pull qwen2.5:3b
```

**"Service connection refused"**
```bash
# Start service first:
python3 ollama_orchestrator/tools/task_breaker_service.py
```

## 🎓 Learning Path

1. Read this file (you are here)
2. Run: `python3 test_task_breaker.py`
3. Try: `python3 ollama_orchestrator/task_breaker.py --prompt "Build a web app"`
4. Copy: Example from `examples_task_breaker.py`
5. Integrate: Into your own scripts

## 📚 More Info

- Full documentation: `ollama_orchestrator/TASK_BREAKER_README.md`
- Feature code: `ollama_orchestrator/task_breaker.py`
- Service code: `ollama_orchestrator/tools/task_breaker_service.py`

---

**Ready to start?** Run this now:
```bash
python3 test_task_breaker.py
```
