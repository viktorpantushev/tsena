#!/usr/bin/env python3
"""
Task Breaker HTTP Service.

This service exposes the task breaking functionality via HTTP.
It allows other services and orchestrators to request task decomposition
without needing to call ollama directly.

Usage:
  python3 tools/task_breaker_service.py

Then call:
  curl -X POST http://127.0.0.1:5001/break-task \
    -H "Content-Type: application/json" \
    -d '{"task": "Build a web application", "model": "qwen2.5:3b"}'
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json
from task_breaker import break_down_task, format_task_breakdown


class Handler(BaseHTTPRequestHandler):
    """HTTP handler for task breaking requests."""

    def _set_json(self, code=200):
        """Set JSON response headers."""
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def do_POST(self):
        """Handle POST requests for task breaking."""
        parsed = urlparse(self.path)

        if parsed.path != "/break-task":
            self._set_json(404)
            self.wfile.write(
                json.dumps({"error": "endpoint not found"}).encode()
            )
            return

        # Read request body
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as e:
            self._set_json(400)
            self.wfile.write(
                json.dumps({"error": f"Invalid JSON: {str(e)}"}).encode()
            )
            return

        # Validate required fields
        if "task" not in request_data:
            self._set_json(400)
            self.wfile.write(
                json.dumps({"error": "Missing required field: 'task'"}).encode()
            )
            return

        task_description = request_data["task"]
        model = request_data.get("model", "qwen2.5:3b")
        temperature = request_data.get("temperature", 0.3)
        max_retries = request_data.get("max_retries", 3)

        try:
            # Break down the task with retry support
            breakdown = break_down_task(
                task_description=task_description,
                model=model,
                temperature=temperature,
                max_retries=max_retries,
            )

            # Format response
            response = {
                "status": "success",
                "original_prompt": breakdown.original_prompt,
                "total_estimated_hours": breakdown.total_estimated_hours,
                "task_count": len(breakdown.tasks),
                "tasks": [
                    {
                        "title": task.title,
                        "description": task.description,
                        "difficulty": task.difficulty,
                        "estimated_hours": task.estimated_hours,
                        "dependencies": task.dependencies,
                    }
                    for task in breakdown.tasks
                ],
            }

            self._set_json(200)
            self.wfile.write(json.dumps(response, indent=2).encode())

        except Exception as e:
            self._set_json(500)
            self.wfile.write(
                json.dumps(
                    {
                        "error": "Task breaking failed",
                        "details": str(e),
                    }
                ).encode()
            )

    def do_GET(self):
        """Handle GET requests - provide status or help."""
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._set_json(200)
            self.wfile.write(
                json.dumps(
                    {
                        "status": "healthy",
                        "service": "task-breaker",
                    }
                ).encode()
            )
            return

        if parsed.path == "/":
            self._set_json(200)
            self.wfile.write(
                json.dumps(
                    {
                        "service": "task-breaker",
                        "endpoints": {
                            "POST /break-task": "Break down a task into subtasks",
                            "GET /health": "Health check",
                        },
                        "example_request": {
                            "task": "Build a real-time chat application",
                            "model": "qwen2.5:3b",
                            "temperature": 0.3,
                        },
                    }
                ).encode()
            )
            return

        self._set_json(404)
        self.wfile.write(json.dumps({"error": "endpoint not found"}).encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run(addr="127.0.0.1", port=5001):
    """Start the HTTP server."""
    server = HTTPServer((addr, port), Handler)
    print(f"Task Breaker Service running on {addr}:{port}")
    print(f"Visit http://{addr}:{port}/ for endpoint information")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Task Breaker HTTP Service")
    parser.add_argument(
        "--addr",
        default="127.0.0.1",
        help="Address to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Port to bind to (default: 5001)",
    )

    args = parser.parse_args()
    run(addr=args.addr, port=args.port)
