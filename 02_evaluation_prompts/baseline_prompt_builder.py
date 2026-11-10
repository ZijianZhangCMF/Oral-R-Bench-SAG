"""Current baseline builder using the shared label-free generation protocol."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generation_protocol import build_baseline_prompts


def _build_prompts(question: str, question_format: str, options: str) -> tuple[str, str]:
    return build_baseline_prompts(question, question_format, options)
