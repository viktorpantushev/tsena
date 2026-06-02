# Task Breaker: LLM-Powered Task Decomposition

Task Breaker is a powerful feature that uses a small LLM to automatically decompose complex tasks into smaller, manageable subtasks with difficulty ratings and time estimates.

## Features

- **🎯 Automatic Task Decomposition**: Break down complex projects into actionable subtasks
- **📊 Difficulty Rating**: Each task gets a 1-5 difficulty score
- **⏱️ Time Estimation**: Estimated hours for each task
- **🔗 Dependency Tracking**: Identifies task dependencies and ordering
- **💬 Plain Language Processing**: LLM responds in natural language, not JSON
- **🌐 HTTP Service**: Expose as a microservice for orchestrator integration
- **🔄 Automatic Retry Logic**: Automatically retries if parsing fails
- **�🔀 LLM Integration**: Works seamlessly with your ollama models

## How It Works

1. **Plain Language Request**: Task Breaker asks the LLM to break down a task in natural language with a clear format
2. **Structured Response**: The LLM provides output with task titles, descriptions, difficulty levels, and time estimates in an easy-to-parse format
3. **Intelligent Parsing**: The tool parses the natural language response to extract task information
4. **Structured Objects**: Task information is converted to Python objects and can be worked with programmatically or displayed nicely

## Output Format

The LLM naturally formats its response like this:

```
1. Task One Title
Description of what needs to be done here.
Difficulty: 2
Estimated: 3.5 hours

2. Task Two Title
Description here
Difficulty: 4
Estimated: 8 hours
Depends on: Task One Title
```

This is then automatically parsed into structured Task objects.

### 1. Command Line Usage (Direct)

Break down a task directly:

```bash
python3 ollama_orchestrator/task_breaker.py \
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
   Description: Create user registration and login endpoints with password hashing

3. Design database schema
   Difficulty: 🔴🔴🔴⚪⚪ (3/5)
   Estimated: 4.0 hours
   Description: Design tables for users, messages, rooms, and connections
   Dependencies: Set up project structure and dependencies

...
```

### 2. JSON Output

Get structured JSON output for programmatic use:

```bash
python3 ollama_orchestrator/task_breaker.py \
  --prompt "Build a REST API" \
  --json > tasks.json
```

### 3. HTTP Service

Start the Task Breaker as a microservice:

```bash
# Terminal 1: Start the service
python3 ollama_orchestrator/tools/task_breaker_service.py
# Service runs on http://127.0.0.1:5001

# Terminal 2: Call the service
curl -X POST http://127.0.0.1:5001/break-task \
  -H "Content-Type: application/json" \
  -d '{"task": "Build a web application", "model": "qwen2.5:3b"}'
```

### 4. Orchestrator Integration

Use Task Breaker within the full orchestrator workflow:

```bash
# Terminal 1: Start task breaker service
python3 ollama_orchestrator/tools/task_breaker_service.py

# Terminal 2: Start orchestrator
python3 ollama_orchestrator/examples/orchestrator_with_task_breaker.py \
  --prompt "Build a REST API with authentication and database"
```

This will:
1. Break down the project into tasks
2. Analyze each task's difficulty
3. Generate a comprehensive project plan
4. Suggest parallelization opportunities

## API Reference

### Command Line Interface

```bash
python3 ollama_orchestrator/task_breaker.py [options]

Options:
  --prompt TEXT           [required] The task description to break down
  --model TEXT           Model to use (default: OLLAMA_MODEL env var or qwen2.5:3b)
  --temperature FLOAT     Temperature for LLM (default: 0.3, lower = more deterministic)
  --max-retries INT       Maximum retries on parsing failure (default: 3)
  --json                 Output as JSON instead of formatted text
```

### Python API

```python
from ollama_orchestrator.task_breaker import break_down_task, Task, TaskBreakdown

# Simple usage
breakdown = break_down_task("Build a web application")

# Access the results
for task in breakdown.tasks:
    print(f"{task.title}: Difficulty {task.difficulty}/5 ({task.estimated_hours}h)")
    print(f"  Dependencies: {task.dependencies}")

# Custom model, temperature, and retries
breakdown = break_down_task(
    "Complex project description",
    model="larger-model:latest",
    temperature=0.5,
    max_retries=5  # Retry up to 5 times on invalid control characters
)

print(f"Total time: {breakdown.total_estimated_hours} hours")
```

## Automatic Retry Logic

The Task Breaker includes built-in retry logic that automatically handles parsing errors:

### How Retries Work

1. **Detection**: If parsing fails or no tasks are found, the operation fails gracefully
2. **Adaptive Prompting**: On retries, the prompt becomes more explicit with examples and strict formatting rules
3. **Cleanup**: Invalid control characters are automatically removed from the response
4. **Max Attempts**: By default, up to 3 attempts are made. This is configurable

### Adaptive Prompts

**First Attempt**: Standard prompt that asks for clean, numbered task breakdown
- Includes examples of expected format
- Focuses on clear structure

**Retry Attempts**: More explicit about format requirements
- Even stricter formatting expectations
- More detailed example
- Emphasizes numbering and field ordering

This approach significantly improves success rates when the LLM initially produces unexpected output.

### Retry Behavior

```python
# Automatic retries on failure
breakdown = break_down_task(task, max_retries=5)  # Will retry up to 5 times

# Disable retries (fail fast)
breakdown = break_down_task(task, max_retries=1)  # No retries, fail on first error
```

### CLI Usage with Retries

```bash
# Use default 3 retries with adaptive prompting
python3 ollama_orchestrator/task_breaker.py --prompt "Your task"

# Custom retry count
python3 ollama_orchestrator/task_breaker.py --prompt "Your task" --max-retries 5

# Output shows retry attempts with prompt type:
# ⚠️  Attempt 1 failed (structured prompt next): ... Retrying...
# ⚠️  Attempt 2 failed (more explicit prompt next): ... Retrying...
```

### HTTP Service with Adaptive Prompts

```bash
curl -X POST http://127.0.0.1:5001/break-task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Your project description",
    "model": "qwen2.5:3b",
    "max_retries": 5
  }'
```

The service automatically uses improved prompts on retries.

### Temperature Adjustment During Retries

Each retry attempt increases the temperature slightly (by 0.1) to encourage more variation in the model's output, which can help avoid repeated parsing failures:

- Attempt 1: temperature = 0.3 (default, most deterministic)
- Attempt 2: temperature = 0.4 (if first fails, more variation)
- Attempt 3: temperature = 0.5 (if second fails, even more variation)

This helps avoid the same parsing error occurring repeatedly by getting slightly different reformatted responses.

### HTTP Service API

#### Break Task (POST)

```
POST /break-task
Content-Type: application/json

Request Body:
{
  "task": "Build a real-time chat application",
  "model": "qwen2.5:3b",           // optional, defaults to qwen2.5:3b
  "temperature": 0.3               // optional, defaults to 0.3
}

Response (200 OK):
{
  "status": "success",
  "original_prompt": "Build a real-time chat application",
  "total_estimated_hours": 45.5,
  "task_count": 8,
  "tasks": [
    {
      "title": "Set up project structure",
      "description": "Create project directory and initialize dependencies",
      "difficulty": 1,
      "estimated_hours": 1.5,
      "dependencies": []
    },
    {
      "title": "Implement authentication",
      "description": "Create user authentication system",
      "difficulty": 3,
      "estimated_hours": 8.0,
      "dependencies": ["Set up project structure"]
    }
  ]
}

Response (500 Error):
{
  "error": "Task breaking failed",
  "details": "Error message from LLM or service"
}
```

#### Health Check (GET)

```
GET /health

Response:
{
  "status": "healthy",
  "service": "task-breaker"
}
```

#### Service Info (GET)

```
GET /

Response:
{
  "service": "task-breaker",
  "endpoints": {...},
  "example_request": {...}
}
```

## Data Models

### Task

```python
@dataclass
class Task:
    title: str                    # Task name
    description: str              # What needs to be done
    difficulty: int               # 1-5 scale
    estimated_hours: float        # Estimated time to complete
    dependencies: list[str]       # List of task titles this depends on
```

### TaskBreakdown

```python
@dataclass
class TaskBreakdown:
    original_prompt: str          # Original task description
    tasks: list[Task]             # Decomposed tasks
    total_estimated_hours: float  # Sum of all estimated hours
```

## Understanding Difficulty Ratings

- **1️⃣ Trivial** (🔴⚪⚪⚪⚪): Straightforward, well-documented, minimal decision-making
- **2️⃣ Easy** (🔴🔴⚪⚪⚪): Standard implementations, good existing patterns
- **3️⃣ Medium** (🔴🔴🔴⚪⚪): Some complexity, requires planning, moderate problem-solving
- **4️⃣ Hard** (🔴🔴🔴🔴⚪): Complex logic, poor documentation, significant design decisions
- **5️⃣ Very Hard** (🔴🔴🔴🔴🔴): Cutting-edge, unclear requirements, potential unknown unknowns

## Plain Language Parsing

The Task Breaker automatically extracts task information from natural language using intelligent pattern matching:

- **Titles**: Identified by numbered/bulleted list markers (1., -, •, *)
- **Descriptions**: Text under task titles that doesn't contain metadata keywords
- **Difficulty**: Detected from lines containing "difficulty: [1-5]" or "difficulty [1-5]"
- **Time Estimates**: Extracted from lines with "estimated: X hours" or "time: X hours"
- **Dependencies**: Found in lines mentioning "depends on:", "prerequisite:", or "requires:"

If metadata is missing from the LLM response, sensible defaults are used:
- Default difficulty: 3 (medium)
- Default time: 2.0 hours
- Default dependencies: empty list

## Model Recommendations

- **Small/Fast**: `qwen2.5:3b` (default) - Good for quick decomposition
- **Balanced**: `mistral:7b` - Better task understanding, more thoughtful decomposition
- **Advanced**: `llama2:13b` or larger - Complex project analysis with sophisticated planning

## Examples

### Example 1: Web Application

```bash
python3 ollama_orchestrator/task_breaker.py \
  --prompt "Create a todo list SPA with user accounts and real-time sync" \
  --model mistral:7b
```

### Example 2: Data Pipeline Project

```bash
python3 ollama_orchestrator/task_breaker.py \
  --prompt "Build an ETL pipeline that processes CSV files and loads into PostgreSQL" \
  --json > pipeline_tasks.json
```

### Example 3: CI/CD Integration

Use in Python scripts for programmatic task planning:

```python
from ollama_orchestrator.task_breaker import break_down_task

def plan_sprint(project_description):
    breakdown = break_down_task(project_description)
    
    # Sort by difficulty
    easy_tasks = [t for t in breakdown.tasks if t.difficulty <= 2]
    hard_tasks = [t for t in breakdown.tasks if t.difficulty >= 4]
    
    print(f"Easy wins: {len(easy_tasks)} tasks")
    print(f"Challenging: {len(hard_tasks)} tasks")
    
    return breakdown
```

## Troubleshooting

### Service connection refused

**Problem**: `Failed to call task breaker service`

**Solution**: Make sure the service is running:
```bash
python3 ollama_orchestrator/tools/task_breaker_service.py
```

### No tasks parsed from response

**Problem**: `No tasks could be parsed from response`

**Solution**: The LLM output format wasn't recognized. Try with a different model:
```bash
python3 ollama_orchestrator/task_breaker.py \
  --prompt "Your task" \
  --model mistral:7b \
  --max-retries 5
```

The parser looks for numbered/bulleted lists. Make sure your prompt is clear about expecting a numbered breakdown.

### Model not found

**Problem**: `Ollama CLI error: model not found`

**Solution**: Pull the model first:
```bash
ollama pull qwen2.5:3b
# or your chosen model
```

### Parsing output with unusual formatting

**Problem**: LLM returns well-formatted output but parsing still fails

**Solution**: The parser is flexible and accepts various formats. If it's still not working, check:
1. The response has numbered/bulleted task headers
2. Difficulty and time estimates include keywords like "difficulty:" and "hours"
3. Run with `--max-retries 5` to get more attempts with adapted prompts

## Performance Tips

1. **Use smaller models for speed**: `qwen2.5:3b` or `phi:2b` respond quickly in natural language
2. **Lower temperature for consistency**: Temperature 0.1-0.3 for more structured, easier-to-parse output
3. **Cache results**: Save breakdowns as JSON for repeated use
4. **Run service mode**: Use HTTP service for multiple requests to avoid startup overhead
5. **Plain language is faster**: No JSON validation overhead, just straightforward pattern matching
6. **First attempt usually succeeds**: Plain language retry logic typically needs 0-1 retries vs. multiple with JSON

## Integration with Orchestrator

The Task Breaker integrates naturally with the orchestrator ecosystem:

```python
# In your examples/orchestrator_with_tools.py
from task_breaker_service import call_task_breaker

# Have the LLM decide to use task breaking
if "<USE_TASK_BREAKER>" in llm_response:
    breakdown = call_task_breaker(extracted_task)
    # Feed back to LLM for planning
```

## Future Enhancements

Potential improvements:
- Priority scoring based on task dependencies
- Resource allocation recommendations
- Risk assessment for complex tasks
- Effort estimation with confidence intervals
- Integration with project management tools
