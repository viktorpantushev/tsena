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
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=None)
def ollama_supports_flag(flag: str) -> bool:
    proc = subprocess.run(["ollama", "run", "--help"], capture_output=True, text=True)
    if proc.returncode != 0:
        return False
    help_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return flag in help_text


def get_smallest_generative_model(fallback: str = "qwen2.5:3b") -> str:
    """Return the name of the smallest generative (non-embedding) model from ollama list."""
    try:
        proc = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if proc.returncode != 0:
            return fallback

        seen_ids: set[str] = set()
        models: list[tuple[str, float]] = []
        for line in proc.stdout.strip().split("\n")[1:]:  # skip header
            parts = line.split()
            if len(parts) < 4:
                continue
            name, model_id = parts[0], parts[1]
            if "embed" in name.lower():
                continue
            if model_id in seen_ids:
                continue
            seen_ids.add(model_id)
            try:
                size_val = float(parts[2])
                unit = parts[3].upper()
                size_gb = size_val / 1024 if unit == "MB" else size_val
                models.append((name, size_gb))
            except (ValueError, IndexError):
                continue

        if not models:
            return fallback
        models.sort(key=lambda x: x[1])
        return models[0][0]
    except Exception:
        return fallback


def get_largest_generative_model(fallback: str = "mistral:7b") -> str:
    """Return the name of the largest generative (non-embedding) model from ollama list."""
    try:
        proc = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if proc.returncode != 0:
            return fallback

        seen_ids: set[str] = set()
        models: list[tuple[str, float]] = []
        for line in proc.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            name, model_id = parts[0], parts[1]
            if "embed" in name.lower():
                continue
            if model_id in seen_ids:
                continue
            seen_ids.add(model_id)
            try:
                size_val = float(parts[2])
                unit = parts[3].upper()
                size_gb = size_val / 1024 if unit == "MB" else size_val
                models.append((name, size_gb))
            except (ValueError, IndexError):
                continue

        if not models:
            return fallback
        models.sort(key=lambda x: x[1], reverse=True)
        return models[0][0]
    except Exception:
        return fallback


def run_ollama_with_tokens(
    model: str,
    prompt: str,
    temperature: Optional[float] = None,
) -> tuple[str, int, int]:
    """Call Ollama REST API; returns (response_text, prompt_tokens, response_tokens).

    Falls back to CLI (token counts = 0) if the REST API is unreachable.
    """
    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if temperature is not None:
        payload["options"] = {"temperature": temperature}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return (
            result.get("response", ""),
            result.get("prompt_eval_count", 0),
            result.get("eval_count", 0),
        )
    except urllib.error.URLError:
        text = run_ollama(model, prompt, temperature=temperature)
        return text, 0, 0


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
    parser.add_argument("--model", default=None, help="Explicit model name. Takes precedence over --model-size.")
    parser.add_argument("--model-size", choices=["smallest", "largest"], default="largest", help="Pick the smallest or largest available generative model (default: largest).")
    parser.add_argument("--prompt", required=True, help="Prompt to send to the model")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="Request JSON output from the CLI if supported")

    args = parser.parse_args()

    if args.model:
        model = args.model
    elif os.environ.get("OLLAMA_MODEL"):
        model = os.environ["OLLAMA_MODEL"]
    elif args.model_size == "smallest":
        model = get_smallest_generative_model()
    else:
        model = get_largest_generative_model()

    if args.json:
        out = run_ollama_json(model, args.prompt, temperature=args.temperature, max_tokens=args.max_tokens)
        print(json.dumps(out, indent=2))
    else:
        print(run_ollama(model, args.prompt, temperature=args.temperature, max_tokens=args.max_tokens))


if __name__ == "__main__":
    main()
