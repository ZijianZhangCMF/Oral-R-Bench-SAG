from __future__ import annotations
import argparse, json, os, re, sys, threading, time
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import requests

MODEL = os.environ.get('ORALSAG_MODEL', 'qwen3.5-27b')
BASE_URL = os.environ.get('ORALSAG_BASE_URL', 'https://yungpt.com/v1')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generation_protocol import (
    ANSWER_REQUIREMENTS, PROTOCOL_VERSION, gate_feedback, generation_context,
    serialize_context, validate_generation_request,
)

STRATEGY_NAME = 'SAG-' + PROTOCOL_VERSION
# The earlier effective_v3_instructions.json remains an archival record.
globals().update(json.loads(Path(__file__).with_name('label_free_instructions.json').read_text()))
DECISION_DRAFT_SYSTEM += "\n\n" + ANSWER_REQUIREMENTS
FINAL_DECISION_SYSTEM += "\n\n" + ANSWER_REQUIREMENTS

class KeyPool:
    def __init__(self, keys: list[str], concurrency_per_key: int):
        self.keys = keys
        self._cycle_index = 0
        self._lock = threading.Lock()
        self._semaphores = {key: threading.Semaphore(concurrency_per_key) for key in keys}

    def acquire_key(self) -> tuple[str, threading.Semaphore]:
        with self._lock:
            key = self.keys[self._cycle_index % len(self.keys)]
            self._cycle_index += 1
        return key, self._semaphores[key]

def parse_json_payload(raw: str) -> Any:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer) + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    raise ValueError("No JSON object or array found")

def qwen_chat(
    key_pool: KeyPool,
    system: str,
    user: str,
    *,
    timeout: int,
    max_tokens: int,
    retries: int = 6,
) -> dict[str, Any]:
    """Call the Yungpt-compatible endpoint and return content plus audit data."""
    validate_generation_request(system, user)
    endpoint = BASE_URL.rstrip("/") + "/chat/completions"
    last_error = ""
    started = time.perf_counter()
    for attempt in range(retries):
        key, semaphore = key_pool.acquire_key()
        with semaphore:
            try:
                response = requests.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "temperature": 0.0,
                        "max_tokens": max_tokens,
                    },
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                response = None

        if response is None:
            time.sleep(min(2 ** attempt, 20))
            continue
        if response.status_code == 429:
            last_error = "HTTP 429"
            time.sleep(min(2 ** (attempt + 1), 45))
            continue
        if response.status_code != 200:
            last_error = f"HTTP {response.status_code}: {response.text[:240]}"
            time.sleep(min(2 ** attempt, 20))
            continue

        try:
            payload = response.json()
            message = payload["choices"][0]["message"]
            content = message.get("content") or ""
            usage = payload.get("usage") or {}
            return {
                "content": content,
                "raw": payload,
                "usage": {
                    "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                    "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
                    "total_tokens": int(usage.get("total_tokens", 0) or 0),
                },
                "latency_sec": round(time.perf_counter() - started, 3),
                "attempts": attempt + 1,
            }
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            last_error = f"invalid response: {type(exc).__name__}: {exc}"
            time.sleep(min(2 ** attempt, 20))

    return {
        "content": "",
        "raw": {},
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "latency_sec": round(time.perf_counter() - started, 3),
        "attempts": retries,
        "error": last_error or "request failed",
    }

common=SimpleNamespace(KeyPool=KeyPool,qwen_chat=qwen_chat,parse_json_payload=parse_json_payload)

def _v2_normalize_gate(gate: str, payload: dict[str, Any]) -> dict[str, Any]:
    if gate == "safety":
        verdict = str(payload.get("verdict", "")).lower()
        if verdict not in {"safe", "needs_revision"}:
            raise ValueError("missing valid safety verdict")
        return {
            "verdict": verdict,
            "risk_level": payload.get("risk_level", "low"),
            "critical_risks": list(payload.get("critical_risks") or [])[:6],
            "must_fix": list(payload.get("must_fix") or [])[:6],
            "do_not_add": list(payload.get("do_not_add") or [])[:6],
            "confidence": payload.get("confidence", "low"),
        }
    if "priority_additions" not in payload:
        raise ValueError("missing priority_additions")
    return {
        "essential_elements": list(payload.get("essential_elements") or [])[:8],
        "covered_elements": list(payload.get("covered_elements") or [])[:8],
        "priority_additions": list(payload.get("priority_additions") or [])[:3],
        "remove_as_nonessential": list(payload.get("remove_as_nonessential") or [])[:5],
        "confidence": payload.get("confidence", "low"),
    }

def normalize_gate(gate: str, payload: dict):
    if gate == "safety":
        return _v2_normalize_gate(gate, payload)
    required = [
        "task_components",
        "core_required",
        "covered_core",
        "missing_core",
        "sequence_requirements",
        "safety_critical_omissions",
        "high_value_support",
        "do_not_expand",
    ]
    if any(key not in payload for key in required):
        raise ValueError("missing completeness coverage field")
    return {
        "task_components": list(payload.get("task_components") or [])[:8],
        "core_required": list(payload.get("core_required") or [])[:8],
        "covered_core": list(payload.get("covered_core") or [])[:8],
        "missing_core": list(payload.get("missing_core") or [])[:5],
        "sequence_requirements": list(payload.get("sequence_requirements") or [])[:8],
        "safety_critical_omissions": list(payload.get("safety_critical_omissions") or [])[:6],
        "high_value_support": list(payload.get("high_value_support") or [])[:3],
        "do_not_expand": list(payload.get("do_not_expand") or [])[:6],
        "confidence": payload.get("confidence", "low"),
    }

def format_requirement(item=None):
    """The same answer requirements apply to every item and generation arm."""
    return ANSWER_REQUIREMENTS

def item_prompt(item: dict[str, Any]) -> str:
    return serialize_context(generation_context(item))

def gate_prompt(item: dict[str, Any], draft: dict[str, Any]) -> str:
    return serialize_context({
        **generation_context(item),
        "decision_draft": draft.get("response", ""),
    })

def final_prompt(
    item: dict[str, Any],
    draft: dict[str, Any],
    safety: dict[str, Any],
    completeness: dict[str, Any],
) -> str:
    return serialize_context({
        **generation_context(item),
        "decision_draft": draft.get("response", ""),
        "safety_gate": gate_feedback("safety_gate", safety.get("result", {})),
        "completeness_gate": gate_feedback("completeness_gate", completeness.get("result", {})),
    })

def call_with_content_retry(
    key_pool: common.KeyPool,
    system: str,
    user: str,
    args: argparse.Namespace,
    max_tokens: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for _ in range(2):
        result = common.qwen_chat(
            key_pool,
            system,
            user,
            timeout=args.timeout,
            max_tokens=max_tokens,
        )
        if result.get("content", "").strip():
            return result
    return result

def run_decision_draft(item: dict[str, Any], key_pool: common.KeyPool, args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    call = call_with_content_retry(key_pool, DECISION_DRAFT_SYSTEM, item_prompt(item), args, 1200)
    return {
        "question_id": item.get("question_id", ""),
        "generation_protocol": PROTOCOL_VERSION,
        "level": item.get("level", ""),
        "agent": "decision_draft",
        "response": call.get("content", ""),
        "agent_call": {key: value for key, value in call.items() if key != "raw"},
        "error": call.get("error", "") if call.get("content", "").strip() else call.get("error", "empty draft"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
    }

def run_gate(
    item: dict[str, Any],
    draft: dict[str, Any],
    gate: str,
    key_pool: common.KeyPool,
    args: argparse.Namespace,
) -> dict[str, Any]:
    started = time.perf_counter()
    system = SAFETY_GATE_SYSTEM if gate == "safety" else COMPLETENESS_GATE_SYSTEM
    call: dict[str, Any] = {}
    parsed: dict[str, Any] = {}
    error = ""
    for _ in range(2):
        call = common.qwen_chat(key_pool, system, gate_prompt(item, draft), timeout=args.timeout, max_tokens=900)
        try:
            payload = common.parse_json_payload(call.get("content", ""))
            if not isinstance(payload, dict):
                raise ValueError("gate output is not an object")
            parsed = normalize_gate(gate, payload)
            error = ""
            break
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            error = f"{type(exc).__name__}: {exc}"
    return {
        "question_id": item.get("question_id", ""),
        "generation_protocol": PROTOCOL_VERSION,
        "level": item.get("level", ""),
        "agent": f"{gate}_gate",
        "result": parsed,
        "raw_output": call.get("content", ""),
        "agent_call": {key: value for key, value in call.items() if key != "raw"},
        "error": error or call.get("error", ""),
        "elapsed_sec": round(time.perf_counter() - started, 3),
    }

def run_final_decision(
    item: dict[str, Any],
    draft: dict[str, Any],
    safety: dict[str, Any],
    completeness: dict[str, Any],
    key_pool: common.KeyPool,
    args: argparse.Namespace,
) -> dict[str, Any]:
    started = time.perf_counter()
    call = call_with_content_retry(
        key_pool,
        FINAL_DECISION_SYSTEM,
        final_prompt(item, draft, safety, completeness),
        args,
        1400,
    )
    return {
        "question_id": item.get("question_id", ""),
        "generation_protocol": PROTOCOL_VERSION,
        "level": item.get("level", ""),
        "model": MODEL,
        "strategy": STRATEGY_NAME,
        "response": call.get("content", ""),
        "agent_call": {key: value for key, value in call.items() if key != "raw"},
        "error": call.get("error", "") if call.get("content", "").strip() else call.get("error", "empty final answer"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
    }

