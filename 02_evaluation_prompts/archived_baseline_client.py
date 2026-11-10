"""MultiModelInferenceTool — Dispatch using the current label-free protocol.

Transport is adapted from the archived client; prompt construction is corrected
for new runs and does not describe the inputs of historical responses.

Supports:
- Loading model configs from models.json (keys + base_url + model type)
- Round-robin key rotation with per-key semaphore concurrency control
- Reasoning models (captures both content and reasoning_content)
- Batch inference: dispatch all items × all models concurrently via ThreadPoolExecutor
- Single-item inference for agent use
"""

import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generation_protocol import (
    PROTOCOL_VERSION, build_baseline_prompts, validate_generation_request,
)

logger = logging.getLogger(__name__)

# ── Config & Key Management ────────────────────────────────────────────────

_config_cache: dict | None = None
_key_index: dict[str, int] = {}
_key_lock = threading.Lock()
_key_semaphores: dict[str, threading.Semaphore] = {}

CONCURRENCY_PER_KEY = 10  # Max concurrent requests per API key


def _load_config() -> dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_path = Path(__file__).parent.parent / "config" / "models.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            _config_cache = json.load(f)
    else:
        _config_cache = {"base_url": "", "models": []}
    return _config_cache


def _get_model_config(model_name: str) -> dict | None:
    config = _load_config()
    for m in config.get("models", []):
        if m["name"] == model_name:
            return m
    return None


def _get_next_key(model_name: str, keys: list[str]) -> str:
    """Round-robin key selection, thread-safe."""
    with _key_lock:
        idx = _key_index.get(model_name, 0)
        key = keys[idx % len(keys)]
        _key_index[model_name] = idx + 1
        return key


def _get_semaphore(key: str) -> threading.Semaphore:
    """Get or create a per-key semaphore to limit concurrency."""
    with _key_lock:
        if key not in _key_semaphores:
            _key_semaphores[key] = threading.Semaphore(CONCURRENCY_PER_KEY)
        return _key_semaphores[key]


# ── Core inference function (used by both single & batch) ──────────────────

def _call_model(
    question: str,
    model_name: str,
    question_format: str = "open-ended",
    options: str = "",
    base_url: str = "",
    api_key: str = "",
    question_id: str = "",
    max_retries: int = 10,
) -> dict:
    """Send one question to one model. Retries ALL errors with exponential backoff."""
    from openai import OpenAI

    config = _load_config()
    model_cfg = _get_model_config(model_name)
    is_reasoning = model_cfg.get("type") == "reasoning" if model_cfg else False
    max_tokens = 4096 if is_reasoning else 2048
    resolved_url = base_url or config.get("base_url", "") or os.getenv("OPENAI_BASE_URL", "")

    system_prompt, user_prompt = _build_prompts(question, question_format, options)
    validate_generation_request(system_prompt, user_prompt)

    last_error = ""
    for attempt in range(max_retries):
        # Rotate key each attempt
        if api_key:
            resolved_key = api_key
        elif model_cfg and model_cfg.get("keys"):
            resolved_key = _get_next_key(model_name, model_cfg["keys"])
        else:
            resolved_key = os.getenv("OPENAI_API_KEY", "")

        sem = _get_semaphore(resolved_key)
        sem.acquire()
        try:
            client = OpenAI(api_key=resolved_key, base_url=resolved_url)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                timeout=180,
            )
            msg = response.choices[0].message
            content = msg.content or ""
            reasoning_content = getattr(msg, "reasoning_content", None) or ""

            result = {
                "question_id": question_id,
                "generation_protocol": PROTOCOL_VERSION,
                "model": model_name,
                "response": content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            }
            if reasoning_content:
                result["reasoning_content"] = reasoning_content
            if attempt > 0:
                result["retries"] = attempt
            return result

        except Exception as e:
            last_error = str(e)
            # Exponential backoff: 2, 4, 8, 16... capped at 60s
            wait = min(2 ** (attempt + 1), 60)
            if attempt < max_retries - 1:
                logger.warning(f"[{model_name}] {question_id} attempt {attempt+1} failed: {last_error[:80]}. Retry in {wait}s")
                time.sleep(wait)
        finally:
            sem.release()

    return {"question_id": question_id, "model": model_name, "error": last_error, "retries": max_retries, "generation_protocol": PROTOCOL_VERSION}


def _build_prompts(question: str, question_format: str, options: str) -> tuple[str, str]:
    return build_baseline_prompts(question, question_format, options)


# ── Batch inference (standalone function, not a CrewAI tool) ───────────────

def batch_inference(
    items: list[dict],
    models: list[str] | None = None,
    base_url: str = "",
    max_workers: int = 0,
    output_dir: str = "./data/inference",
) -> dict[str, list[dict]]:
    """Run inference on all items × all models with maximum concurrency.

    Args:
        items: List of QA items, each with question_id, question, question_format, options.
        models: List of model names. If None, use all models from config.
        base_url: Override base URL.
        max_workers: Max threads. 0 = auto (num_keys × CONCURRENCY_PER_KEY).
        output_dir: Directory to save results.

    Returns:
        Dict mapping model_name -> list of result dicts.
    """
    config = _load_config()
    items_by_id = {item.get("question_id", ""): item for item in items}
    if models is None:
        models = [m["name"] for m in config.get("models", [])]

    # Calculate max workers: sum of (keys × concurrency_per_key) across all models
    if max_workers <= 0:
        total_keys = 0
        for model_name in models:
            mcfg = _get_model_config(model_name)
            total_keys += len(mcfg["keys"]) if mcfg and mcfg.get("keys") else 1
        max_workers = min(total_keys * CONCURRENCY_PER_KEY, 500)

    logger.info(f"Batch inference: {len(items)} items × {len(models)} models = {len(items) * len(models)} requests, max_workers={max_workers}")

    # Build all tasks
    futures = {}
    results: dict[str, list[dict]] = {m: [] for m in models}
    errors = []

    os.makedirs(output_dir, exist_ok=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for model_name in models:
            for item in items:
                future = executor.submit(
                    _call_model,
                    question=item.get("question", ""),
                    model_name=model_name,
                    question_format=item.get("question_format", "open-ended"),
                    options=item.get("options", []),
                    base_url=base_url,
                    question_id=item.get("question_id", ""),
                )
                futures[future] = (model_name, item.get("question_id", ""))

        completed = 0
        total = len(futures)
        for future in as_completed(futures):
            completed += 1
            model_name, qid = futures[future]
            try:
                result = future.result()
                results[model_name].append(result)
                if "error" in result:
                    errors.append(result)
            except Exception as e:
                errors.append({"model": model_name, "question_id": qid, "error": str(e)})

            if completed % 100 == 0 or completed == total:
                err_count = len(errors)
                logger.info(f"Progress: {completed}/{total} ({completed*100//total}%) errors={err_count}")

    # ── Retry pass: re-run all failed items ────────────────────────────────
    if errors:
        logger.info(f"Retry pass: {len(errors)} failed items, waiting 30s before retry...")
        time.sleep(30)

        # Build lookup: items by question_id
        items_by_id = {item.get("question_id", ""): item for item in items}

        retry_tasks = []
        for err in errors:
            qid = err.get("question_id", "")
            mname = err.get("model", "")
            if qid in items_by_id:
                retry_tasks.append((mname, items_by_id[qid]))

        if retry_tasks:
            logger.info(f"Retrying {len(retry_tasks)} failed requests...")
            retry_errors = []

            with ThreadPoolExecutor(max_workers=min(max_workers, 50)) as executor:
                retry_futures = {}
                for mname, item in retry_tasks:
                    future = executor.submit(
                        _call_model,
                        question=item.get("question", ""),
                        model_name=mname,
                        question_format=item.get("question_format", "open-ended"),
                        options=item.get("options", []),
                        base_url=base_url,
                        question_id=item.get("question_id", ""),
                        max_retries=10,
                    )
                    retry_futures[future] = (mname, item.get("question_id", ""))

                for future in as_completed(retry_futures):
                    mname, qid = retry_futures[future]
                    try:
                        result = future.result()
                        if "error" not in result:
                            # Replace the error entry in results
                            results[mname] = [r for r in results[mname] if not (r.get("question_id") == qid and "error" in r)]
                            results[mname].append(result)
                        else:
                            retry_errors.append(result)
                    except Exception as e:
                        retry_errors.append({"model": mname, "question_id": qid, "error": str(e)})

            errors = retry_errors
            logger.info(f"After retry: {len(errors)} still failed")

    # Save results per model
    for model_name, model_results in results.items():
        safe_name = model_name.replace("/", "_").replace(":", "_")
        out_path = os.path.join(output_dir, f"{safe_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(model_results, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(model_results)} results to {out_path}")

    if errors:
        err_path = os.path.join(output_dir, "_errors.json")
        with open(err_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(errors)} errors to {err_path}")

    # Export OpenAI Evals JSONL
    evals_dir = os.path.join(os.path.dirname(output_dir), "exports", "openai_evals")
    os.makedirs(evals_dir, exist_ok=True)
    for model_name, model_results in results.items():
        safe_name = model_name.replace("/", "_").replace(":", "_")
        evals_path = os.path.join(evals_dir, f"{safe_name}.jsonl")
        with open(evals_path, "w", encoding="utf-8") as f:
            for r in model_results:
                source_item = items_by_id[r.get("question_id", "")]
                system, user = _build_prompts(
                    source_item["question"], "", source_item.get("options", []),
                )
                line = {
                    "input": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "ideal": "",
                    "output": r.get("response", ""),
                    "metadata": {
                        "generation_protocol": PROTOCOL_VERSION,
                        "question_id": r.get("question_id", ""),
                        "model": model_name,
                        "finish_reason": r.get("finish_reason", ""),
                    },
                }
                f.write(json.dumps(line, ensure_ascii=False) + "\n")

    summary = {
        "total_requests": len(items) * len(models),
        "completed": sum(len(v) for v in results.values()),
        "errors": len(errors),
        "models": {m: len(v) for m, v in results.items()},
    }
    logger.info(f"Batch inference complete: {json.dumps(summary)}")
    return results


# ── CrewAI Tool (single-item, for agent use) ───────────────────────────────

class InferenceInput(BaseModel):
    question: str = Field(..., description="The question text to send to the model.")
    model_name: str = Field(default="gpt-4o", description="Model identifier.")
    question_format: str = Field(
        default="open-ended",
        description="One of: multiple-choice, open-ended, metacognitive-open, metacognitive-analysis.",
    )
    options: str = Field(default="", description="JSON-encoded list of MC options, if applicable.")
    base_url: str = Field(default="", description="Override API base URL. Empty = use config/env default.")
    api_key: str = Field(default="", description="Override API key. Empty = use config/env default.")


class MultiModelInferenceTool(BaseTool):
    name: str = "multi_model_inference"
    description: str = (
        "Send a QA item to an LLM via OpenAI-compatible API and return the response. "
        "Automatically loads API keys from models.json with round-robin rotation. "
        "Supports reasoning models (captures reasoning_content). "
        "For batch inference across all models, use batch_inference() directly."
    )
    args_schema: Type[BaseModel] = InferenceInput

    def _run(
        self,
        question: str,
        model_name: str = "gpt-4o",
        question_format: str = "open-ended",
        options: str = "",
        base_url: str = "",
        api_key: str = "",
    ) -> str:
        result = _call_model(
            question=question,
            model_name=model_name,
            question_format=question_format,
            options=options,
            base_url=base_url,
            api_key=api_key,
        )
        return json.dumps(result, ensure_ascii=False)
