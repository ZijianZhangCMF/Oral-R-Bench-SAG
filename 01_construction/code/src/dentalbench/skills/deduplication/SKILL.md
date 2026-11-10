---
name: deduplication
description: >
  Detect and remove duplicate or near-duplicate QA items from the OralBench dataset
  using semantic similarity thresholds and structured metadata comparison. Use after
  QA generation and factuality review to ensure each item in the benchmark tests a
  distinct piece of knowledge.
metadata:
  author: OralBench Team
  version: "1.0"
---

# Deduplication

## Scope

Identify and resolve duplicate or near-duplicate QA items in the OralBench dataset. Duplicates inflate benchmark size without adding discriminative value and can bias evaluation scores toward over-represented topics.

---

## Duplicate Detection Pipeline

### Step 1: Exact Match Detection

Compare `question` fields after normalization:

1. Lowercase the text.
2. Remove all punctuation and extra whitespace.
3. Strip common prefixes ("which of the following", "what is the", "describe the").
4. If two normalized question strings are identical, mark as exact duplicates.

### Step 2: Semantic Similarity Detection

Compute pairwise semantic similarity for all items within the same `dimension`:

1. Encode each item's `question` field using the project's configured sentence embedding model.
2. Compute cosine similarity between all pairs within the same dimension.
3. Flag pairs with cosine similarity > 0.85 as candidate duplicates.

Do NOT compute cross-dimension similarity. Two items in different dimensions that happen to mention the same disease are not duplicates if they test different competencies.

### Step 3: Metadata-Aware Filtering

For each candidate duplicate pair, check whether they test the same knowledge from the same angle:

1. Compare `dimension` values. If different, they are NOT duplicates even if similarity > 0.85.
2. Compare `knowledge_type` values. If different, they are NOT duplicates.
3. Compare `difficulty` values. Same concept at different difficulty levels may both be valid.
4. Compare `question_format` values. The same concept as MC and open-ended may both be valid.

Apply this decision matrix:

| Same dimension | Same knowledge_type | Same difficulty | Same format | Verdict |
|:-:|:-:|:-:|:-:|:--|
| Yes | Yes | Yes | Yes | Duplicate — remove one |
| Yes | Yes | Yes | No | Keep both (different format tests different skills) |
| Yes | Yes | No | Yes | Keep both if difficulty gap >= 2 levels; otherwise flag for review |
| Yes | Yes | No | No | Keep both |
| No | - | - | - | Not duplicates |
| - | No | - | - | Not duplicates |

---

## Duplicate Resolution: Which Item to Keep

When a duplicate pair is confirmed, keep the item that scores highest on this priority list (evaluate in order, use the first criterion that breaks the tie):

1. **More complete metadata**: the item with more non-empty fields in `source_reference`, `evaluation_criteria`, and `explanation`.
2. **Higher difficulty**: prefer the harder item, as harder items are more costly to generate and more valuable for benchmark discrimination.
3. **Better source reference**: prefer the item with a DOI or specific page reference over one with only a title.
4. **Earlier question_id**: if all else is equal, keep the item with the lower sequence number to maintain stability.

Record the removed item's `question_id` in a deduplication log with the reason and the ID of the kept item.

---

## Deduplication Log Format

```json
{
  "deduplication_run": {
    "timestamp_utc": "2026-04-09T10:00:00Z",
    "total_items_before": 1650,
    "exact_duplicates_removed": 12,
    "semantic_duplicates_removed": 34,
    "total_items_after": 1604,
    "pairs": [
      {
        "kept": "OB_D2_OMUC_042",
        "removed": "OB_D2_OMUC_187",
        "similarity": 0.92,
        "reason": "semantic duplicate; kept item has DOI in source_reference"
      }
    ]
  }
}
```

---

## Similarity Threshold Rationale

- **> 0.85**: duplicate. The questions test the same knowledge point with minor wording variation.
- **0.75 - 0.85**: review zone. Manually inspect to determine if the items test the same concept from different clinical angles.
- **< 0.75**: not duplicates. No action needed.

Do NOT lower the threshold below 0.85 without explicit justification. Lowering it risks removing items that test the same concept from legitimately different clinical angles.

---

## Constraints

- Do NOT remove items that test the same concept but from different clinical angles. Example: "What nerve innervates the lower teeth?" and "During an inferior alveolar nerve block, which nerve is targeted?" both involve the IAN but test different competencies (anatomy vs. procedure). These are NOT duplicates.
- Do NOT compute similarity across different dimensions. A D1 item and a D5 item about the same disease are not duplicates.
- Do NOT remove both items in a duplicate pair. Always keep exactly one.
- Do NOT deduplicate across different `knowledge_type` values. A Factual and a Conceptual question about the same topic serve different purposes.
- Do NOT use only exact string matching. Paraphrased duplicates are the primary concern.
- Do NOT modify item content during deduplication. This skill only removes items; content revision is handled by other skills.
- Always produce the deduplication log. Do NOT silently remove items.
