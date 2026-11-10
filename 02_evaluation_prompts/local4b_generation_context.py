"""Shared input for both local generation arms; metadata remains local."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generation_protocol import generation_context


def context(item, format_req=True):
    # Keep the legacy argument for callers; it never changes the model input.
    return generation_context(item)
