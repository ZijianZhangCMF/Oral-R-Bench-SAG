def build_rows() -> list[dict[str, str]]:
    items = {row["question_id"]: row for row in load_json(FULL / "sample_full_open_ended_items.json")}
    responses = {row["question_id"]: row for row in load_json(FULL / "sag_responses.json")}
    if set(items) != set(responses) or len(items) != 1713:
        raise RuntimeError("Full SAG items and responses do not match")
    rows = []
    for qid in sorted(items):
        item = items[qid]
        response = responses[qid]["response"]
        rows.append({
            "question_id": qid,
            "question": (item.get("question") or "")[:1600],
            "knowledge_type": item.get("knowledge_type", ""),
            "dimension": item.get("dimension", ""),
            "question_format": item.get("question_format", ""),
            "reference_answer": (item.get("reference_answer") or item.get("answer") or "")[:4000],
            "model_response": response[:5000],
        })
    return rows
