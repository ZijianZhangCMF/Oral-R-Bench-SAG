from __future__ import annotations
import json
from typing import Any

DIMS=['factuality', 'completeness', 'efficiency', 'clarity', 'accuracy']

def strip_json_payload(raw: str) -> Any:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("[")
    end = text.rfind("]") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])

    raise ValueError("No JSON array/object found")

def normalize_scores(payload: Any, expected_qids: set[str]) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("results", "scores", "items", "evaluations"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
        else:
            payload = [payload]

    if not isinstance(payload, list):
        raise ValueError("Judge output is not a list")

    normalized: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        qid = str(item.get("question_id", "")).strip()
        if qid not in expected_qids:
            continue

        row: dict[str, Any] = {"question_id": qid}
        ok = True
        for dim in DIMS:
            try:
                val = int(round(float(item.get(dim))))
            except Exception:
                ok = False
                break
            if not 1 <= val <= 5:
                ok = False
                break
            row[dim] = val

        try:
            safety = int(round(float(item.get("safety"))))
        except Exception:
            ok = False
            safety = 1
        if safety not in (0, 1):
            ok = False

        if ok:
            row["safety"] = safety
            row["safety_issue"] = str(item.get("safety_issue", "") or "")
            criteria_summary = item.get("criteria_summary")
            if isinstance(criteria_summary, dict):
                row["criteria_summary"] = criteria_summary
            else:
                row["criteria_summary"] = {}
            caps = item.get("caps_applied")
            if isinstance(caps, list):
                row["caps_applied"] = [str(cap) for cap in caps][:8]
            elif caps:
                row["caps_applied"] = [str(caps)]
            else:
                row["caps_applied"] = []
            confidence = str(item.get("judge_confidence", "") or "").lower()
            row["judge_confidence"] = confidence if confidence in {"high", "medium", "low"} else ""
            normalized.append(row)

    return normalized

def build_prompt(items: list[dict[str, str]]) -> str:
    compact = json.dumps(items, ensure_ascii=False, indent=2)
    return (
        f"Evaluate these {len(items)} OralBench model responses.\n"
        "Use the rubric from the system message. Return ONLY the JSON array.\n\n"
        f"Items:\n{compact}"
    )

def build_eval_item(qid: str, benchmark: dict[str, Any], inference: dict[str, str]) -> dict[str, str]:
    meta = benchmark[qid]
    return {
        "question_id": qid,
        "question": (meta.get("question", "") or "")[:800],
        "knowledge_type": meta.get("knowledge_type", ""),
        "dimension": meta.get("dimension", ""),
        "question_format": meta.get("question_format", ""),
        "reference_answer": (meta.get("reference_answer") or meta.get("answer", "") or "")[:1200],
        "model_response": (inference.get(qid, "") or "")[:1200],
    }

def extract_mc(text: str) -> str:
    text = (text or "").strip()
    if text and text[0] in "ABCD":
        return text[0]
    match = re.search(r"\b([A-D])\b", text)
    return match.group(1) if match else ""

