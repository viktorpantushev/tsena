#!/usr/bin/env python3
"""
LLM Discussion Orchestrator

This script runs a short moderated discussion between two LLM participants
and then asks a third LLM (the judge) to decide who won. The judge is asked
to return JSON with `winner` and `reason`.

Usage example:
  python3 ollama_orchestrator/orchestrator_discussion.py \
    --topic "Should cities prioritize public transit over roads?" \
    --rounds 4 \
    --modelA qwen2.5:3b --modelB qwen2.5:3b --judge qwen2.5:3b

Notes:
- This uses the local `ollama` CLI; ensure `ollama` is installed and models
  (e.g., `qwen2.5:3b`) are available.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Dict, List, Optional, Tuple


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


def parse_tool_call(output: str) -> Optional[Tuple[str, Dict[str, str]]]:
    match = re.search(r"CALL\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(.*)", output)
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


def parse_model_json(output: str) -> dict:
    try:
        return json.loads(output)
    except Exception:
        start = output.find("{")
        end = output.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(output[start:end+1])
            except Exception as e:
                raise RuntimeError(f"Failed to parse JSON: {e}\nOutput:\n{output}")
        raise RuntimeError(f"Failed to parse JSON from model output. Raw output:\n{output}")


def build_system_prompt(participant_name: str, stance: str) -> str:
    return (
        f"You are {participant_name}. You take the position: {stance}."
        " Keep responses concise (1-3 short paragraphs). Address the opponent's points when possible."
        " On each turn, you must check the remaining discussion length first by calling the discussion_length tool before you answer."
    )


def call_discussion_length(current_turn: int, max_turns: int, base_url: str = "http://127.0.0.1:5000") -> str:
    url = f"{base_url}/remaining?" + urllib.parse.urlencode({"current_turn": current_turn, "max_turns": max_turns})
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read().decode()


def run_discussion(topic: str, modelA: str, modelB: str, judge: str, rounds: int = 4, temperature: float = 0.3, max_tokens: Optional[int] = 256) -> None:
    # roles
    stanceA = "Pro (in favor)"
    stanceB = "Con (against)"

    sysA = build_system_prompt("Participant A", stanceA)
    sysB = build_system_prompt("Participant B", stanceB)

    history: List[str] = []

    # Opening instruction for first speaker
    opening = (
        "Topic: {topic}\n"
        "You have {max_turns} total speaker turns in this debate.\n"
        "Before you answer, you must call the tool to check remaining turns:\n"
        "  CALL discussion_length current_turn={current_turn} max_turns={max_turns}\n"
        "After the tool returns the count, continue your response.\n"
        "Please begin with a brief opening statement representing your stance."
    )

    def run_agent(model: str, system_prompt: str, participant_name: str, history: List[str], current_turn: int, max_turns: int) -> str:
        context = system_prompt + "\n\nConversation so far:\n" + "\n".join(history) + "\n"
        if current_turn == 0:
            prompt = context + opening.format(topic=topic, current_turn=current_turn, max_turns=max_turns)
        else:
            prompt = (
                context
                + f"Current turn: {current_turn} of {max_turns}.\n"
                + f"You must call the tool before replying: CALL discussion_length current_turn={current_turn} max_turns={max_turns}\n"
                + "Then continue your response as the next speaker."
            )
        out = run_ollama(model, prompt, temperature=temperature, max_tokens=max_tokens).strip()

        steps = 0
        while True:
            steps += 1
            if steps > 4:
                raise RuntimeError("Too many tool-call iterations from the model.")
            tool_call = parse_tool_call(out)
            if not tool_call:
                return out

            tool, args = tool_call
            if tool != "discussion_length":
                raise RuntimeError(f"Unsupported tool requested: {tool}")

            current_turn = int(args.get("current_turn", current_turn))
            max_turns = int(args.get("max_turns", max_turns))
            print("\n=== TOOL USED ===")
            print(f"Participant: {participant_name}")
            print(f"Tool: discussion_length")
            print(f"current_turn={current_turn}, max_turns={max_turns}")
            tool_out = call_discussion_length(current_turn, max_turns)
            print(f"Tool result: {tool_out.strip()}")
            print("=== END TOOL ===\n")
            follow_up = (
                context
                + "Tool result returned:\n"
                + tool_out.strip()
                + "\nRespond to the user or call the tool again if needed.\n"
            )
            out = run_ollama(model, follow_up, temperature=temperature, max_tokens=max_tokens).strip()

    max_turns = rounds * 2
    outA = run_agent(modelA, sysA, "Participant A", history, current_turn=0, max_turns=max_turns)
    print("Participant A:\n", outA)
    history.append(f"A: {outA}")

    # Alternate turns
    for r in range(1, rounds + 1):
        current_turn = len(history)
        outB = run_agent(modelB, sysB, "Participant B", history, current_turn=current_turn, max_turns=max_turns)
        print(f"\nParticipant B (round {r}):\n", outB)
        history.append(f"B: {outB}")

        if r >= rounds:
            break

        current_turn = len(history)
        outA = run_agent(modelA, sysA, "Participant A", history, current_turn=current_turn, max_turns=max_turns)
        print(f"\nParticipant A (round {r}):\n", outA)
        history.append(f"A: {outA}")

    # After discussion, call judge
    convo_text = "\n".join(history)
    judge_system = (
        "You are the impartial judge of a short debate between Participant A (Pro) and Participant B (Con).\n"
        "Read the conversation and decide who presented the stronger case. Output JSON only with the keys: winner, reason."
        " winner must be one of: 'A', 'B', or 'Tie'. Keep reason brief.\n"
    )

    judge_prompt = judge_system + "\nConversation:\n" + convo_text + "\n\nRespond with JSON only."
    judge_out = run_ollama(judge, judge_prompt, temperature=0.0, max_tokens=512)
    print("\nJudge output (raw):\n", judge_out)

    try:
        j = parse_model_json(judge_out)
    except Exception as e:
        print("Failed to parse judge JSON:", e)
        return

    winner = j.get("winner")
    reason = j.get("reason")
    print(f"\nJudge decision: {winner}\nReason: {reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM discussion orchestrator")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--rounds", type=int, default=2, help="Number of reply rounds (each round includes a reply by B and optionally A)")
    parser.add_argument("--modelA", default=None, help="Model for participant A (env OLLAMA_MODELA or default qwen2.5:3b)")
    parser.add_argument("--modelB", default=None, help="Model for participant B (env OLLAMA_MODELB or default qwen2.5:3b)")
    parser.add_argument("--judge", default=None, help="Model for judge (env OLLAMA_JUDGE or default qwen2.5:3b)")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    modelA = args.modelA or os.environ.get("OLLAMA_MODELA", os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"))
    modelB = args.modelB or os.environ.get("OLLAMA_MODELB", os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"))
    judge = args.judge or os.environ.get("OLLAMA_JUDGE", os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"))

    run_discussion(args.topic, modelA, modelB, judge, rounds=args.rounds, temperature=args.temperature, max_tokens=args.max_tokens)


if __name__ == "__main__":
    main()
