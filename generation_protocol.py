"""Shared model-visible input contract for baseline and Oral-SAG.

Benchmark metadata stays in local records and never selects a prompt variant.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

PROTOCOL_VERSION = "label-free-generation-v1"

ANSWER_REQUIREMENTS = (
    "Answer every explicit task in the question. "
    "For a question that asks you to select one of the supplied lettered options, "
    "return only the selected option letter. Otherwise, return concise bullet points, "
    "one key conclusion or action per bullet, with enough points to cover the task. "
    "Preserve the order of clinical actions when the question requires a sequence. "
    "When the question explicitly requests confidence, give confidence (0-100%) "
    "in the first bullet. State relevant uncertainty and limitations. "
    "Do not include your reasoning process, invented patient details, citations, "
    "exact doses, or unsupported thresholds."
)
BASELINE_SYSTEM = "You are a dental medicine specialist.\n\n" + ANSWER_REQUIREMENTS

# Reject recognizable benchmark annotations in supplied text instead of silently
# rewriting clinical content. Ordinary clinical uses of D/L codes are not erased.
_ANNOTATION = re.compile(
    r"\bOB_D(?:10|[1-9])_[A-Za-z0-9_-]+\b|"
    r"(?im:^\s*(?:question_id|knowledge_type|question_format|dimension|level)\s*[:=])"
)
_ITEM_FIELDS = {"question", "options"}
_STAGE_FIELDS = _ITEM_FIELDS | {"decision_draft", "safety_gate", "completeness_gate"}
_GATE_FIELDS = {
    "safety_gate": {
        "verdict", "risk_level", "critical_risks", "must_fix", "do_not_add", "confidence",
    },
    "completeness_gate": {
        "task_components", "core_required", "covered_core", "missing_core",
        "sequence_requirements", "safety_critical_omissions", "high_value_support",
        "do_not_expand", "confidence",
    },
}


def _check_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("Model-visible text must be a string")
    if _ANNOTATION.search(text):
        raise ValueError("Benchmark annotation in model-visible text; remove it upstream")
    return text


def generation_context(item: Mapping[str, Any]) -> dict[str, Any]:
    """Allow only question text and answer options, irrespective of metadata."""
    question = _check_text(item["question"])
    if not question.strip():
        raise ValueError("Question must not be empty")
    out: dict[str, Any] = {"question": question}
    options = item.get("options")
    if options is None or options == "" or options == []:
        return out
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except json.JSONDecodeError:
            options = options.splitlines()
    if not isinstance(options, (list, tuple)):
        raise TypeError("Options must be a list of strings or a JSON-encoded list")
    if options:
        out["options"] = [_check_text(option) for option in options]
    return out


def gate_feedback(stage: str, result: Mapping[str, Any]) -> dict[str, Any]:
    """Keep gate feedback fields, excluding local bookkeeping and extra keys."""
    if not isinstance(result, Mapping):
        raise TypeError("Gate feedback must be an object")
    fields = _GATE_FIELDS[stage]
    out = {key: value for key, value in result.items() if key in fields}
    for value in out.values():
        if isinstance(value, list):
            for entry in value:
                _check_text(entry)
        else:
            _check_text(value)
    return out


def validate_generation_request(system: str, user: str) -> None:
    """Fail closed at the transport boundary on unexpected context fields."""
    _check_text(system)
    payload = json.loads(user)
    if not isinstance(payload, dict) or set(payload) - _STAGE_FIELDS:
        raise ValueError("Unexpected model-visible generation fields")
    canonical = generation_context(payload)
    if "decision_draft" in payload:
        canonical["decision_draft"] = _check_text(payload["decision_draft"])
    for stage in _GATE_FIELDS:
        if stage in payload:
            canonical[stage] = gate_feedback(stage, payload[stage])
    if canonical != payload:
        raise ValueError("Generation payload contains noncanonical or extra fields")


def serialize_context(payload: Mapping[str, Any]) -> str:
    user = json.dumps(payload, ensure_ascii=False, indent=2)
    validate_generation_request("", user)
    return user


def build_baseline_prompts(
    question: str, question_format: str = "open-ended", options: Any = "",
) -> tuple[str, str]:
    """Build a shared prompt; question_format does not affect the request."""
    return BASELINE_SYSTEM, serialize_context(
        generation_context({"question": question, "options": options})
    )
