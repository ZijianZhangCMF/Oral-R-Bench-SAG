---
name: exam-parsing
description: Parse Chinese dental licensing exam questions from paired .docx files into structured English-language JSON. Use when converting raw exam documents into seed QA pairs for OralBench.
metadata:
  author: OralBench Team
  version: "2.0.0"
---

# Exam Parsing

## Input

Accept paired Microsoft Word (.docx) files:
- `X-题目.docx` — contains exam questions in Simplified Chinese
- `X-解析.docx` — contains answer explanations in Simplified Chinese

Both files must be present. If the explanation file is missing, set `"correct_answer": null` and `"explanation": ""` for all questions and add `"answer_key_missing": true` at the top level.

## Output Schema

Produce one JSON object per document pair:

```json
{
  "source_document": "2023_oral_practitioner_unit3-题目.docx",
  "exam_year": 2023,
  "exam_type": "practitioner",
  "questions": [
    {
      "question_stem": "A 45-year-old female presents with bilateral white reticular lesions on the buccal mucosa...",
      "options": ["Oral leukoplakia", "Oral lichen planus", "Oral candidiasis", "Discoid lupus erythematosus", "White sponge nevus"],
      "correct_answer": "B",
      "explanation": "Bilateral symmetric reticular white lesions with burning sensation are characteristic of oral lichen planus...",
      "subject": "oral mucosal diseases"
    }
  ],
  "parsing_stats": {
    "total_detected": 150,
    "successfully_parsed": 148,
    "answer_matched": 145,
    "failed": 2,
    "failed_question_numbers": [67, 112]
  }
}
```

The `options` array MUST be ordered A through E (index 0 = A, index 1 = B, etc.). Most questions have 5 options; some have 4.

## Parsing Procedure

### 1. Preprocess Documents

1. Read the .docx file using a library that preserves formatting (e.g., python-docx).
2. Extract all paragraphs with style information (heading levels, bold, numbering).
3. Strip headers, footers, watermarks, and page numbers.

### 2. Detect Question Boundaries

Identify where each question starts and ends using these patterns:

| Pattern | Purpose |
|---------|---------|
| `^\d+[.、．]\s*` | Question number prefix |
| `^[A-E][.、．]\s*` | Option prefix |
| `答案[：:]\s*[A-E]` | Inline answer |
| `【答案】[A-E]` | Bracketed answer |
| `解析[：:]` | Explanation marker |
| `共用题干` or `病例摘要` | Case-linked set header |
| `以下提问` | Sub-question section marker |

Rules:
- A new question starts when a new number sequence appears after a complete option set (A through D or E).
- A paragraph without option markers followed by options is a question stem.
- A paragraph over 100 characters without option markers followed by numbered sub-questions indicates a case-linked set (A3/A4 type). Group sub-questions under a shared `case_context` field.

### 3. Extract Components

For each question, extract:
- `question_number` — original numbering from the document
- `question_type` — classify as A1 (single-best-answer), A2 (clinical vignette), A3/A4 (case-linked), or B (matching)
- `question_stem` — the question text
- `options` — ordered list of answer choices
- `correct_answer` — letter of the correct answer
- `explanation` — rationale from the explanation document
- `case_context` — shared clinical scenario (A3/A4 only)

### 4. Match Answers

Search for correct answers in this priority order:
1. Inline markers in the question document: `答案[：:]?\s*[A-E]`, `【答案】[A-E]`, `正确答案[：:]?\s*[A-E]`
2. Separate answer section at the end of the question document, matched by question number.
3. The companion explanation document (`X-解析.docx`), matched by question number.

Flag any question where no answer could be matched.

### 5. Translate to English

Translate every field to English. Follow these rules strictly:

- Use internationally recognized medical nomenclature (ICD-11, MeSH preferred terms).
- Use INN (International Nonproprietary Name) for drug names.
- Keep numerical values and units unchanged unless non-standard Chinese units are used.
- If a Chinese medical concept has no direct English equivalent, provide the closest term with a bracketed note: `"pericoronitis [智齿冠周炎]"`.
- Transliterate proper nouns (author names, institution names). Do NOT translate them.
- Keep option letters (A–E) unchanged.

Common translation mappings:
- 口腔扁平苔藓 → "oral lichen planus" (NOT "oral flat moss lichen")
- 复发性阿弗他溃疡 → "recurrent aphthous ulcer"
- 牙周炎 → "periodontitis"
- 颞下颌关节 → "temporomandibular joint"

### 6. Tag Metadata

Add to each question:
- `subject` — inferred from content (e.g., "oral mucosal diseases", "periodontics", "oral surgery")
- `source_question_number` — original number
- `exam_year` — from document name or content
- `exam_type` — "practitioner" (执业医师) or "assistant" (助理医师)

## Validation Rules

1. Every question must have at least 4 options (A–D). Flag questions with fewer.
2. The `correct_answer` letter must correspond to an existing option index.
3. No question may have an empty `question_stem` after translation.
4. For every 50th question, include original Chinese in a `translation_check` field for human review.
5. Flag questions with >90% stem similarity (post-translation) as potential duplicates.
6. A3/A4 case-linked questions must have at least 2 sub-questions sharing the same `case_context`.

## Error Handling

- If a question cannot be parsed, log it in `parsing_stats.failed` with the question number and skip it.
- If translation is uncertain for a medical term, add a `translation_notes` field with both the English attempt and original Chinese.
- If the document contains images in question stems (e.g., radiographs), add `"has_image": true` to that question.

## Constraints

- Do NOT add information not present in the source documents.
- Do NOT merge separate questions into one.
- Do NOT fabricate explanations when the explanation document lacks one — use empty string.
- Do NOT reorder options — preserve the original A–E sequence.
- Do NOT process embedded images — only note their presence.
