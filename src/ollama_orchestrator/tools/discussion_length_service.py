#!/usr/bin/env python3
"""
Minimal discussion-length HTTP service.

Usage:
  python3 ollama_orchestrator/tools/discussion_length_service.py

Then call:
  http://127.0.0.1:5000/remaining?current_turn=2&max_turns=6
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json


class Handler(BaseHTTPRequestHandler):
    def _set_json(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/remaining":
            self._set_json(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())
            return

        qs = parse_qs(parsed.query)
        try:
            current_turn = int(qs.get("current_turn", [0])[0])
            max_turns = int(qs.get("max_turns", [0])[0])
        except ValueError:
            self._set_json(400)
            self.wfile.write(json.dumps({"error": "current_turn and max_turns must be integers"}).encode())
            return

        if max_turns < 0 or current_turn < 0:
            self._set_json(400)
            self.wfile.write(json.dumps({"error": "current_turn and max_turns must be non-negative"}).encode())
            return

        remaining = max(max_turns - current_turn, 0)
        self._set_json(200)
        self.wfile.write(json.dumps({"remaining": remaining, "current_turn": current_turn, "max_turns": max_turns}).encode())


def run(addr="127.0.0.1", port=5000):
    server = HTTPServer((addr, port), Handler)
    print(f"Discussion-length service running at http://{addr}:{port}/remaining?current_turn=2&max_turns=6")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")
        server.server_close()


if __name__ == "__main__":
    run()
