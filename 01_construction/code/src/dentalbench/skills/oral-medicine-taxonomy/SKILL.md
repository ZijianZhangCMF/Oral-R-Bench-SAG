---
name: oral-medicine-taxonomy
description: Classify oral medicine content into the OralBench taxonomy (knowledge level, dimension, subspecialty, difficulty). Use when tagging questions, content blocks, or cases for benchmark assembly.
metadata:
  author: OralBench Team
  version: "2.0.0"
---

# Oral Medicine Taxonomy Classification

Assign exactly four labels to every item: Knowledge Level, Dimension, Subspecialty, and Difficulty.

For full definitions of all taxonomy categories, see `references/taxonomy.md`.

## Input

Accept any item with at minimum a `question_stem` or `content` field. Items may also include `options`, `correct_answer`, `explanation`, and `case_context`.

## Output Schema

```json
{
  "question_id": "2023-prac-042",
  "taxonomy": {
    "knowledge_level": {
      "code": "K2",
      "label": "Conceptual",
      "confidence": "certain",
      "rationale": "Requires understanding distinguishing pathological features."
    },
    "dimensions": [
      {"code": "D5", "label": "Differential Diagnosis", "role": "primary", "confidence": "certain"},
      {"code": "D3", "label": "Clinical Presentation", "role": "secondary", "confidence": "probable"}
    ],
    "subspecialty": {
      "code": "S1",
      "label": "Oral Mucosal Diseases",
      "confidence": "certain"
    },
    "difficulty": {
      "code": "L2",
      "label": "Intermediate",
      "confidence": "probable",
      "rationale": "Classic presentation, one reasoning step to differentiate."
    }
  }
}
```

## Classification Flowchart

Follow this exact sequence for every item. Do NOT skip steps.

### Step 1: Assign Knowledge Level (exactly one)

```
Can the item be answered by recalling a single fact, name, number, or definition?
  YES → K1 (Factual)
  NO  ↓
Does it require explaining a mechanism, principle, comparison, or classification rationale?
  YES → K2 (Conceptual)
  NO  ↓
Does it require describing a clinical procedure, protocol, treatment plan, or step sequence?
  YES → K3 (Procedural)
  NO  ↓
Does it require evaluating evidence quality, reflecting on reasoning, or managing diagnostic uncertainty?
  YES → K4 (Metacognitive)
```

If the item spans K2 and K3 (e.g., "explain why this procedure is preferred"), choose the level that represents the primary cognitive demand.

### Step 2: Assign Dimensions (1–3)

Identify which clinical competencies the item tests. Assign a primary dimension first, then up to 2 secondary dimensions.

| Code | Dimension | Assign when the item asks about... |
|------|-----------|-------------------------------------|
| D1 | Disease Identification & Classification | naming, classifying, identifying subtypes |
| D2 | Etiology & Pathogenesis | causes, risk factors, mechanisms |
| D3 | Clinical Presentation & Symptoms | signs, symptoms, typical/atypical features |
| D4 | Diagnostic Methods & Interpretation | test selection, result interpretation, criteria |
| D5 | Differential Diagnosis | generating/narrowing diagnostic possibilities |
| D6 | Treatment Planning & Management | drug selection, surgical approach, protocols |
| D7 | Prognosis & Follow-up | outcomes, recurrence, follow-up schedules |
| D8 | Prevention & Patient Education | prevention, screening, counseling |
| D9 | Systemic-Oral Correlations | oral↔systemic disease relationships |
| D10 | Evidence-Based Practice & Research | evidence appraisal, guideline interpretation |

Rules:
- If a vignette asks "What is the diagnosis AND how would you treat it?", assign both D1/D5 and D6.
- Co-assign D9 whenever a systemic condition is integral, even if the primary dimension is something else.
- Do NOT assign more than 3 dimensions. If more seem applicable, keep only the 3 most relevant.

### Step 3: Assign Subspecialty (exactly one primary, optionally one secondary)

| Code | Subspecialty |
|------|-------------|
| S1 | Oral Mucosal Diseases |
| S2 | Periodontics |
| S3 | Oral & Maxillofacial Surgery |
| S4 | Oral & Maxillofacial Pathology |
| S5 | Oral Radiology & Imaging |
| S6 | Dental Pharmacology & Therapeutics |
| S7 | Pediatric Oral Medicine |
| S8 | Geriatric Oral Medicine |
| S9 | Oral Oncology |
| S10 | Temporomandibular Disorders & Orofacial Pain |

Rules:
- Assign the most specific subspecialty. A histopathology question about oral lichen planus → S1 (disease context dominates), NOT S4.
- Assign a second subspecialty only when the item genuinely requires knowledge from both fields (e.g., surgical management of oral cancer → S3 + S9).
- When a systemic disease causes oral manifestations, assign based on the oral manifestation type (e.g., diabetes-related periodontitis → S2).

### Step 4: Assign Difficulty (exactly one)

```
Is it single-concept recall with no clinical ambiguity?
  YES → L1 (Basic) — target: preclinical dental students
  NO  ↓
Is it a straightforward clinical scenario with classic presentation, 1–2 reasoning steps?
  YES → L2 (Intermediate) — target: clinical students / recent graduates
  NO  ↓
Does it require integrating multiple domains, atypical presentation, or complex management?
  YES → L3 (Advanced) — target: practicing dentists / specialists
  NO  ↓
Does it involve diagnostic uncertainty, conflicting evidence, or expert-level synthesis?
  YES → L4 (Expert) — target: specialists / academic clinicians
```

Rules:
- Difficulty is determined by cognitive demand, NOT disease rarity. A rare disease can be L1 if it only requires name recall.
- When uncertain between two levels, choose the higher level.
- L4 items often (but not always) map to K4 knowledge level.

### Step 5: Record Confidence

For each of the four labels, record confidence as one of:
- `"certain"` — unambiguous classification
- `"probable"` — most likely correct but minor ambiguity exists
- `"uncertain"` — flag for human review

## Constraints

- Do NOT assign more than one knowledge level.
- Do NOT assign more than one difficulty level.
- Do NOT assign more than 3 dimensions.
- Do NOT assign more than 2 subspecialties.
- Do NOT skip the rationale field for knowledge_level and difficulty — it is required.
- Do NOT change taxonomy codes or labels. Use exactly the codes defined in `references/taxonomy.md`.

## Batch Processing

When classifying multiple items, output a JSON array. Maintain consistent classification standards across the batch — do NOT drift in strictness between early and late items.
