---
name: factuality-review
description: >
  Verify medical accuracy of generated QA items against source material, checking answer
  correctness, distractor plausibility, guideline currency, terminology standards, and
  internal consistency. Use after QA generation to gate items before they enter the
  benchmark dataset.
metadata:
  author: OralBench Team
  version: "1.0"
---

# Factuality Review

## Scope

Review every generated QA item for medical accuracy before it enters the OralBench dataset. This skill is the quality gate between generation and inclusion. No item passes without completing this checklist.

---

## Review Checklist

Execute every check in order. An item must pass ALL checks to be approved.

### Check 1: Answer Matches Source

- Locate the source cited in `source_reference`.
- Verify that the `answer` (for MC) or `reference_answer` (for open-ended) is factually supported by the cited source.
- If the source is a textbook, verify the specific page or section.
- If the source is a guideline, verify the recommendation grade and year.
- If the answer contradicts the source, REJECT the item.
- If the source cannot be located or verified, do NOT approve. Flag with `"review_status": "source_unverifiable"` for human review.

### Check 2: All MC Options Are Plausible

- For multiple-choice items, verify that every distractor is a real clinical entity, drug, anatomical structure, or concept from the same domain.
- Verify that no distractor is obviously absurd, humorous, or from an unrelated field.
- Verify that no two options are synonyms or subsume each other.
- Verify that the correct option is not consistently longer or more detailed than distractors.
- If any distractor fails plausibility, REJECT and specify which option and why.

### Check 3: No Outdated Guidelines Cited

- Verify the edition/year of the cited source.
- Cross-check against current versions of key references:
  - WHO Classification of Head and Neck Tumours (5th ed., 2022)
  - AAP/EFP Periodontitis Classification (2018)
  - ADA clinical practice guidelines (check year)
  - NCCN guidelines for head and neck cancers (check current year)
  - AHA antibiotic prophylaxis guidelines (2021 update)
- If the item cites a superseded guideline and the answer has changed in the current version, REJECT.
- If the item cites a superseded guideline but the answer remains unchanged, FLAG with `"review_note": "older source, answer still current"` and approve.

### Check 4: Terminology Is Standard

- Verify that disease names, drug names, and anatomical terms use current standard nomenclature.
- Drug names must use INN (International Nonproprietary Names), not brand names.
- Disease classifications must use current WHO/ICD terminology.
- Anatomical terms must follow Terminologia Anatomica.
- If non-standard terminology is used, REJECT with a correction note.

### Check 5: No Internal Contradictions

- Verify that the `question`, `answer`, `reference_answer`, and `explanation` fields are mutually consistent.
- For MC items: verify that the letter in `answer` corresponds to the correct option in the `options` array.
- For open-ended items: verify that `answer` and `reference_answer` do not contradict each other.
- Verify that the stated difficulty is consistent with the actual cognitive demand (cross-reference with difficulty-calibration skill criteria).
- If any contradiction is found, REJECT with details.

---

## Common Dental Misconceptions to Watch For

Flag and verify items that touch on these frequently confused topics:

1. **Lidocaine maximum dose confusion**: The maximum dose of lidocaine with epinephrine is 7.0 mg/kg (not 4.4 mg/kg, which is the dose WITHOUT epinephrine). Items that confuse these values must be corrected.

2. **Ameloblastoma vs. dentigerous cyst on radiograph**: Both can present as unilocular radiolucencies associated with an impacted tooth. Items must not claim radiographic appearance alone is diagnostic. Biopsy is required for definitive diagnosis.

3. **Oral lichen planus malignant transformation rate**: The commonly cited 1-2% rate is debated and varies by study. Items must not state a single definitive percentage without noting the range and controversy. Acceptable range: 0.5-2.5% over 5-10 years.

4. **Inferior alveolar nerve block failure in mandibular molars with irreversible pulpitis**: Failure rates are 30-80%, not rare. Items that imply IAN block reliably achieves anesthesia in inflamed pulp tissue must be corrected.

5. **Chlorhexidine concentration for oral rinse vs. periodontal irrigation**: Oral rinse is 0.12% (US) or 0.2% (Europe). Subgingival irrigation uses lower concentrations. Items must specify the correct concentration for the stated application.

6. **Bisphosphonate-related osteonecrosis (BRONJ/MRONJ) terminology**: Current preferred term is "medication-related osteonecrosis of the jaw" (MRONJ), which includes denosumab and antiangiogenic agents, not just bisphosphonates. Items using "BRONJ" should be updated to "MRONJ" unless specifically discussing bisphosphonate-only cases.

---

## Review Output Format

For each reviewed item, produce:

```json
{
  "question_id": "OB_D2_OMUC_042",
  "review_status": "approved" | "rejected" | "source_unverifiable" | "needs_revision",
  "checks": {
    "answer_matches_source": true | false,
    "options_plausible": true | false | null,
    "guidelines_current": true | false,
    "terminology_standard": true | false,
    "no_contradictions": true | false
  },
  "rejection_reasons": [],
  "revision_notes": [],
  "reviewer_confidence": "high" | "medium" | "low"
}
```

---

## Decision Rules

- If all 5 checks pass: set `review_status` to `"approved"`.
- If any check fails: set `review_status` to `"rejected"` and populate `rejection_reasons`.
- If the source cannot be verified (Check 1): set `review_status` to `"source_unverifiable"`. Do NOT approve.
- If the item is mostly correct but needs minor wording fixes: set `review_status` to `"needs_revision"` and populate `revision_notes` with specific corrections.
- If reviewer confidence is `"low"` on any check, flag the item for human review regardless of pass/fail status.

---

## Constraints

- Do NOT approve items where the source cannot be verified. Flag them for human review.
- Do NOT approve MC items with fewer than 4 options.
- Do NOT approve items with empty `source_reference`.
- Do NOT approve items where the answer is ambiguous (two options could be argued as correct).
- Do NOT silently correct errors. Always document what was wrong and what the correction is.
- Do NOT rely on general knowledge for verification. Every factual claim must be traceable to the cited source.
- When in doubt, REJECT rather than approve. False negatives (rejecting a good item) are less harmful than false positives (approving an incorrect item).
