---
name: format-validation
description: >
  Validate QA items against the OralBench JSON schema, checking required fields, value
  constraints, ID patterns, and format-specific rules for multiple-choice and open-ended
  items. Use as the final gate before items are committed to the benchmark dataset.
metadata:
  author: OralBench Team
  version: "1.0"
---

# Format Validation

## Scope

Validate every QA item against the OralBench schema before it enters the dataset. This is a structural and syntactic check, not a medical accuracy check (that is handled by factuality-review). An item must pass all validation rules to be included.

---

## Required Fields

Every item must contain all of the following fields with non-null, non-empty values:

| Field | Type | Description |
|-------|------|-------------|
| `question_id` | string | Unique identifier following the pattern `OB_{dimension}_{subspecialty_abbrev}_{number}` |
| `knowledge_type` | string | One of: `"Factual"`, `"Conceptual"`, `"Procedural"`, `"Metacognitive"` |
| `dimension` | string | One of: `"D1"` through `"D10"` |
| `subspecialty` | array of strings | At least one value from the Subspecialty enum |
| `difficulty` | string | One of: `"easy"`, `"medium"`, `"hard"`, `"expert"` |
| `source_type` | string | One of: `"textbook"`, `"guideline"`, `"exam"`, `"case_report"`, `"web"` |
| `source_reference` | object | Must contain `title` (non-empty string) and at least one of `doi_or_url` or `page_or_section` |
| `question_format` | string | One of: `"multiple-choice"`, `"open-ended"`, `"metacognitive-open"`, `"metacognitive-analysis"` |
| `question` | string | The question text (non-empty) |
| `answer` | string | The correct answer (non-empty) |
| `reference_answer` | string | Comprehensive reference answer |
| `language` | string | Must be `"en"` |

---

## question_id Pattern

Format: `OB_{dimension}_{subspecialty_abbrev}_{number}`

- `{dimension}`: `D1` through `D10`
- `{subspecialty_abbrev}`: one of the abbreviations from the table below
- `{number}`: zero-padded 3-digit integer (001-999)

### Subspecialty Abbreviations

| Subspecialty | Abbreviation |
|-------------|-------------|
| Oral Mucosal Diseases | OMUC |
| Periodontology | PERI |
| Oral and Maxillofacial Surgery | OMFS |
| Oral and Maxillofacial Pathology | PATH |
| Oral Radiology and Imaging | RADI |
| Dental Pharmacology and Therapeutics | PHAR |
| Pediatric Oral Medicine | PEDO |
| Geriatric Oral Medicine | GERI |
| Oral Oncology | ONCO |
| Temporomandibular Disorders and Orofacial Pain | TMJP |
| Operative Dentistry and Endodontics | ENDO |
| Prosthodontics | PROS |
| Orthodontics | ORTH |
| Dental Public Health | DEPH |
| Oral Anatomy and Physiology | ANAT |

Regex pattern for validation:
```
^OB_D(1[0]?|[1-9])_[A-Z]{4}_\d{3}$
```

Examples of valid IDs:
- `OB_D1_ANAT_001`
- `OB_D5_OMUC_042`
- `OB_D10_ONCO_003`

Examples of invalid IDs:
- `OB_D1_anat_001` (lowercase abbreviation)
- `OB_D1_ANAT_1` (number not zero-padded)
- `D1_ANAT_001` (missing OB_ prefix)
- `OB_D11_ANAT_001` (invalid dimension)

---

## Format-Specific Validation Rules

### Multiple-Choice Items (`question_format == "multiple-choice"`)

1. `options` must be an array of exactly 4 strings. Do NOT pass items with fewer than 4 options.
2. Each option string must be non-empty.
3. `answer` must be a single uppercase letter: `"A"`, `"B"`, `"C"`, or `"D"`.
4. The letter in `answer` must correspond to a valid index in `options` (A=0, B=1, C=2, D=3).
5. No two options may be identical strings.
6. `reference_answer` must be non-empty (minimum 20 characters).

### Open-Ended Items (`question_format == "open-ended"`)

1. `options` must be an empty array `[]` or absent.
2. `answer` must be a non-empty string (minimum 10 characters).
3. `reference_answer` must be a non-empty string with length > 50 characters. Do NOT pass items where `reference_answer` is shorter than 50 characters.
4. `explanation` must be non-empty.

### Metacognitive-Open Items (`question_format == "metacognitive-open"`)

1. `options` must be an empty array `[]` or absent.
2. `answer` must be non-empty (minimum 10 characters).
3. `reference_answer` must be > 50 characters.
4. `reference_answer` must contain at least 2 of these section markers (case-insensitive): `ANSWER`, `CONFIDENCE`, `LIMITATIONS`, `ALTERNATIVE PERSPECTIVES`.

### Metacognitive-Analysis Items (`question_format == "metacognitive-analysis"`)

1. `options` must be an empty array `[]` or absent.
2. `answer` must be non-empty (minimum 10 characters).
3. `reference_answer` must be > 50 characters.
4. `reference_answer` must contain at least 2 of these section markers (case-insensitive): `ANALYSIS`, `ERRORS IDENTIFIED`, `CORRECTED REASONING`, `DECISION RATIONALE`.

---

## Cross-Field Consistency Rules

1. `dimension` must be consistent with `knowledge_type`:
   - Factual: D1, D2, or D3
   - Conceptual: D4, D5, or D6
   - Procedural: D7 or D8
   - Metacognitive: D9 or D10

2. `difficulty` must respect knowledge_type constraints:
   - Procedural items: do NOT pass with `difficulty == "easy"`
   - Metacognitive items: do NOT pass with `difficulty == "easy"` or `difficulty == "medium"`

3. `subspecialty` values must all be from the Subspecialty enum. Do NOT pass items with unknown subspecialty values.

4. `question_format` must be consistent with `knowledge_type`:
   - Factual and Conceptual: `"multiple-choice"` or `"open-ended"`
   - Procedural: `"multiple-choice"` or `"open-ended"`
   - Metacognitive: `"metacognitive-open"` or `"metacognitive-analysis"`

---

## Validation Output Format

For each validated item, produce:

```json
{
  "question_id": "OB_D2_OMUC_042",
  "valid": true,
  "errors": []
}
```

For a failing item:

```json
{
  "question_id": "OB_D2_OMUC_042",
  "valid": false,
  "errors": [
    {
      "field": "options",
      "rule": "mc_option_count",
      "message": "Multiple-choice item has 3 options; exactly 4 required",
      "severity": "error"
    },
    {
      "field": "reference_answer",
      "rule": "min_length_open_ended",
      "message": "reference_answer is 38 characters; minimum 50 required for open-ended items",
      "severity": "error"
    }
  ]
}
```

---

## Batch Validation Summary

After processing all items, produce:

```json
{
  "validation_summary": {
    "total_items": 1500,
    "valid": 1462,
    "invalid": 38,
    "errors_by_rule": {
      "mc_option_count": 5,
      "mc_answer_letter_invalid": 2,
      "empty_source_reference": 8,
      "reference_answer_too_short": 12,
      "question_id_pattern_mismatch": 4,
      "difficulty_constraint_violation": 3,
      "dimension_knowledge_type_mismatch": 2,
      "duplicate_question_id": 2
    }
  }
}
```

---

## Constraints

- Do NOT pass items with empty `source_reference`. Every item must have a traceable source.
- Do NOT pass MC items with fewer than 4 options.
- Do NOT pass open-ended or metacognitive items where `reference_answer` is shorter than 50 characters.
- Do NOT pass items with `question_id` values that do not match the pattern `OB_{dimension}_{subspecialty_abbrev}_{number}`.
- Do NOT pass items with duplicate `question_id` values. Every ID must be unique across the entire dataset.
- Do NOT silently fix errors. Report every error in the validation output. Fixes are handled by upstream skills.
- Do NOT validate medical accuracy. That is the responsibility of the factuality-review skill.
- Treat every rule violation as blocking. An item with any error is `"valid": false` and must not enter the dataset.
