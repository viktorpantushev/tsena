#!/usr/bin/env python3
"""
Orchestrator demo that shows how an LLM (via `ollama` CLI) can call a
local tool. The orchestrator asks the model to output JSON instructions
when it wants to call a tool. The orchestrator executes the tool and returns
the tool result back to the model until the model returns a final answer.

Usage (start the discussion-length tool in another terminal):
  python3 ollama_orchestrator/tools/discussion_length_service.py

Then run this script:
  python3 ollama_orchestrator/orchestrator_with_tools.py --model <model> --prompt "Calculate 12*(3+4)"
"""

from __future__ import annotations

import os
import re
import subprocess
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Optional, Tuple, Dict


@lru_cache(maxsize=None)
def ollama_supports_flag(flag: str) -> bool:
    proc = subprocess.run(["ollama", "run", "--help"], capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    help_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return flag in help_text


def run_ollama(model: str, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
    cmd = ["ollama", "run", model]
    if temperature is not None and ollama_supports_flag("--temperature"):
        cmd += ["--temperature", str(temperature)]
    if max_tokens is not None and ollama_supports_flag("--max-tokens"):
        cmd += ["--max-tokens", str(max_tokens)]
    cmd.append(prompt)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama CLI error: {proc.stderr.strip()}")
    return proc.stdout


def call_discussion_length(current_turn: int, max_turns: int, base_url: str = "http://127.0.0.1:5000") -> str:
    url = f"{base_url}/remaining?" + urllib.parse.urlencode({"current_turn": current_turn, "max_turns": max_turns})
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read().decode()


def parse_tool_call(output: str) -> Optional[Tuple[str, Dict[str, str]]]:
    match = re.search(r"CALL\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*)", output)
    if not match:
        return None
    tool = match.group(1)
    args_part = match.group(2).strip()
    args: Dict[str, str] = {}
    for token in re.split(r"\s+", args_part):
        if "=" in token:
            key, value = token.split("=", 1)
            args[key] = value
    return tool, args


def orchestrate(model: str, user_prompt: str) -> None:
    # Provide the model with a tool spec and a strict JSON protocol.
    system = (
        "You are an assistant that can call tools.\n"
        "Available tool:\n"
        "- discussion_length: return how many turns are left in the discussion. Endpoint: GET /remaining?current_turn=<int>&max_turns=<int> returning JSON {\"remaining\": int}.\n"
        "Protocol: when you want to call a tool, output a single line in this plain-text format:\n"
        "  CALL discussion_length current_turn=<int> max_turns=<int>\n"
        "Example call: CALL discussion_length current_turn=2 max_turns=6\n"
        "When finished, output your response in plain text.\n"
    )

    prompt = system + "User: " + user_prompt

    # 1) Ask model for first instruction
    out = run_ollama(model, prompt)
    print("Model output:\n", out)

    while True:
        tool_call = parse_tool_call(out)
        if not tool_call:
            print("Final response:", out.strip())
            return

        tool, args = tool_call
        if tool != "discussion_length":
            print("Unknown tool requested:", tool)
            return

        current_turn = args.get("current_turn")
        max_turns = args.get("max_turns")
        if current_turn is None or max_turns is None:
            print("Tool call missing 'current_turn' or 'max_turns' argument")
            return

        tool_out = call_discussion_length(int(current_turn), int(max_turns))
        follow_up = (
            system
            + "Tool result returned:\n"
            + tool_out.strip()
            + "\nContinue your response or call another tool with CALL discussion_length current_turn=<int> max_turns=<int>.\n"
        )
        out = run_ollama(model, follow_up)
        print("Model output:\n", out)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Orchestrator with tool demo")
    parser.add_argument("--model", default=None, help="Model name to run. If not provided, uses OLLAMA_MODEL or 'qwen2.5:3b'.")
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    model = args.model or os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

    orchestrate(model, args.prompt)


if __name__ == "__main__":
    main()
