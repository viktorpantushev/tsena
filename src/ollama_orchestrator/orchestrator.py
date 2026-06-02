#!/usr/bin/env python3
"""
Simple Ollama orchestrator using the `ollama` CLI.

This script calls the `ollama` command-line tool to run a model with a prompt.
It keeps the implementation minimal and dependency-free so it works in most
local setups where `ollama` is installed.
"""

from __future__ import annotations

import json
import os
import subprocess
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=None)
def ollama_supports_flag(flag: str) -> bool:
    proc = subprocess.run(["ollama", "run", "--help"], capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    help_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return flag in help_text


def run_ollama(model: str, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
    """Run `ollama run <model>` with a prompt and return raw stdout.

    This uses the `ollama` CLI. Ensure `ollama` is installed and the model
    is available locally (or accessible).
    """
    # Some versions of the Ollama CLI expect the prompt as a positional
    # argument rather than a `--prompt` flag. Build the command with
    # flags first and append the prompt as the final positional argument.
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


def run_ollama_json(model: str, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> dict:
    """Try to get JSON output (if the CLI supports `--json`).

    Falls back to parsing stdout as JSON and raises on error.
    """
    # Request JSON output (if supported) and pass prompt positionally.
    cmd = ["ollama", "run", model]
    cmd += ["--json"]
    if temperature is not None and ollama_supports_flag("--temperature"):
        cmd += ["--temperature", str(temperature)]
    if max_tokens is not None and ollama_supports_flag("--max-tokens"):
        cmd += ["--max-tokens", str(max_tokens)]
    cmd.append(prompt)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama CLI error: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Simple Ollama orchestrator (CLI) ")
    parser.add_argument("--model", default=None, help="Model name to run (local ollama model). If not provided, uses OLLAMA_MODEL or 'qwen2.5:3b'.")
    parser.add_argument("--prompt", required=True, help="Prompt to send to the model")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="Request JSON output from the CLI if supported")

    args = parser.parse_args()

    model = args.model or os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

    if args.json:
        out = run_ollama_json(model, args.prompt, temperature=args.temperature, max_tokens=args.max_tokens)
        print(json.dumps(out, indent=2))
    else:
        print(run_ollama(model, args.prompt, temperature=args.temperature, max_tokens=args.max_tokens))


if __name__ == "__main__":
    main()
