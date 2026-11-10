"""EmbeddingSimilarityTool — Detect near-duplicate QA items via embedding cosine similarity."""

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class EmbeddingSimilarityInput(BaseModel):
    texts_json: str = Field(
        ...,
        description="JSON string: list of {question_id, text} objects to compare pairwise.",
    )
    threshold: float = Field(default=0.85, description="Cosine similarity threshold for duplicate detection.")


class EmbeddingSimilarityTool(BaseTool):
    name: str = "embedding_similarity"
    description: str = (
        "Compute pairwise cosine similarity between QA item texts to detect duplicates. "
        "Use during QA review to find near-duplicate items above a similarity threshold."
    )
    args_schema: Type[BaseModel] = EmbeddingSimilarityInput

    def _run(self, texts_json: str, threshold: float = 0.85) -> str:
        try:
            items = json.loads(texts_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {e}"})

        if len(items) < 2:
            return json.dumps({"duplicates": [], "message": "Need at least 2 items to compare."})

        try:
            from sentence_transformers import SentenceTransformer, util
        except ImportError:
            return json.dumps({"error": "sentence-transformers not installed. Run: uv add sentence-transformers"})

        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [item.get("text", "") for item in items]
        ids = [item.get("question_id", f"item_{i}") for i, item in enumerate(items)]

        embeddings = model.encode(texts, convert_to_tensor=True)
        cos_scores = util.cos_sim(embeddings, embeddings)

        duplicates = []
        seen = set()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                score = cos_scores[i][j].item()
                if score >= threshold:
                    pair_key = (ids[i], ids[j])
                    if pair_key not in seen:
                        seen.add(pair_key)
                        duplicates.append({
                            "item_a": ids[i],
                            "item_b": ids[j],
                            "similarity": round(score, 4),
                        })

        duplicates.sort(key=lambda x: x["similarity"], reverse=True)
        return json.dumps({"duplicates": duplicates, "total_pairs_checked": len(items) * (len(items) - 1) // 2}, indent=2)
