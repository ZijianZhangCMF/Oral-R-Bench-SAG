---
name: qa-conceptual
description: >
  Generate Level 2 (Conceptual) knowledge QA items covering D4 (Pathological Mechanism),
  D5 (Differential Diagnosis), and D6 (Treatment Rationale), focusing on "why" and "how"
  questions that require reasoning. Use when populating the benchmark with items that test
  understanding of mechanisms, comparisons, and clinical rationale beyond single-fact recall.
metadata:
  author: OralBench Team
  version: "1.1"
---

# QA Conceptual Generation

## Scope

Generate QA items for knowledge_type `"Conceptual"` across three dimensions:

| Dimension | Code | Focus |
|-----------|------|-------|
| Pathological Mechanism | D4 | Molecular/cellular pathogenesis, immunological processes, disease progression pathways |
| Differential Diagnosis | D5 | Distinguishing clinically similar conditions based on key differentiating features |
| Treatment Rationale | D6 | Explaining why a treatment is chosen, mechanism of therapeutic action, evidence basis |

Every item must require reasoning, not recall. If a question can be answered by memorizing a single fact, it belongs in qa-factual, not here.

---

## Source Material

Valid sources for Conceptual items are:

1. **Exam questions** (Chinese dental licensing exams and similar structured exam banks)
2. **PDF sources** (textbooks and clinical guidelines)

When source is exam questions (Chinese dental licensing), use them as INSPIRATION to create original English questions testing the same concepts. Do NOT translate verbatim. Do NOT copy question stems, option lists, or answer explanations from the source exam. Reconstruct the tested concept as a new, original English-language item that requires reasoning about mechanisms, differentials, or rationale.

When source is PDF (textbooks or guidelines), identify the mechanistic explanation, differential reasoning, or treatment rationale and formulate an original question that tests understanding of that reasoning.

Do NOT use case reports as source for conceptual items. Case reports belong to L3/L4 generation only.

---

## Output Schema Requirements

Set these fields on every generated item:

- `knowledge_type`: `"Conceptual"`
- `dimension`: `"D4"`, `"D5"`, or `"D6"`
- `question_format`: `"multiple-choice"` or `"open-ended"`
- `difficulty`: `"easy"`, `"medium"`, `"hard"`, or `"expert"`
- `subspecialty`: one or more values from the `Subspecialty` enum
- `source_type`: `"textbook"`, `"guideline"`, or `"exam"`
- `source_reference`: must include `title` and at least one of `doi_or_url` or `page_or_section`
- `language`: `"en"`

---

## Format Rules

### Multiple-Choice

- Exactly 4 options (A-D), exactly one correct.
- Store correct letter in `answer`.
- Store option texts in `options` as 4 strings without letter prefixes.
- Distractors must represent plausible alternative mechanisms, diagnoses, or rationales.
- Do NOT use "All of the above" or "None of the above."
- Do NOT make the correct option consistently longer than distractors.

### Open-Ended

- Store the question in `question`. Set `options` to `[]`.
- `answer`: concise correct answer (2-4 sentences).
- `reference_answer`: comprehensive answer (4-10 sentences) with mechanistic detail.
- `explanation`: why the answer is correct, what reasoning errors are common.

---

## Question Templates by Dimension

### D4: Pathological Mechanism

Focus on "why does this happen" and "how does this process work" questions.

```
MC Template - D4 Medium (Mechanism Reasoning):
Question: "In oral lichen planus, CD8+ T lymphocytes target basal keratinocytes. Which mechanism best explains the resulting saw-tooth rete ridge pattern seen histologically?"
Options: [
  "Apoptosis of basal cells with compensatory irregular epithelial hyperplasia",
  "Direct lysis of the basement membrane by matrix metalloproteinases",
  "Autoantibody-mediated detachment at the dermal-epidermal junction",
  "Granulomatous inflammation compressing the rete pegs"
]
Answer: "A"

Open-Ended Template - D4 Hard:
Question: "Explain the immunopathological mechanism by which pemphigus vulgaris causes intraepithelial blistering, and contrast this with the mechanism of mucous membrane pemphigoid."
Answer: "In pemphigus vulgaris, IgG autoantibodies target desmoglein-3 on keratinocyte desmosomes, causing acantholysis (loss of cell-cell adhesion) within the suprabasal epithelium. In mucous membrane pemphigoid, autoantibodies target components of the basement membrane zone (BP180, laminin-332), causing subepithelial cleavage..."
```

### D5: Differential Diagnosis

Present symptoms or clinical findings, then ask the model to distinguish between 2-3 conditions.

```
MC Template - D5 Medium (Differential Diagnosis):
Question: "A 50-year-old patient presents with bilateral white reticular lesions on the buccal mucosa. Which feature would most strongly favor a diagnosis of oral lichen planus over chronic cheek biting?"
Options: [
  "Wickham striae with surrounding erythema and a positive direct immunofluorescence showing fibrinogen at the basement membrane",
  "Irregular shredded white tissue along the occlusal line that peels easily",
  "Unilateral distribution confined to the area of dental restoration contact",
  "Resolution of lesions within 2 weeks of eliminating the suspected irritant"
]
Answer: "A"

Open-Ended Template - D5 Hard:
Question: "A patient presents with a painless, white, non-scrapable plaque on the lateral tongue. Describe how you would differentiate between oral leukoplakia, oral hairy leukoplakia, and verrucous carcinoma based on clinical and histological features."
Answer: "Oral leukoplakia is a clinical diagnosis of exclusion — a white plaque that cannot be characterized as any other definable lesion. Oral hairy leukoplakia presents as corrugated white lesions typically on the lateral tongue, associated with EBV, and shows 'balloon cells' and viral cytopathic changes histologically without dysplasia. Verrucous carcinoma presents as a thick, warty, well-differentiated white lesion with broad pushing rete ridges and minimal cytological atypia on biopsy..."
```

### D6: Treatment Rationale

Explain why a treatment is selected, not just what treatment to give.

```
MC Template - D6 Medium (Treatment Rationale):
Question: "Why is systemic corticosteroid therapy preferred over topical corticosteroids as initial treatment for severe pemphigus vulgaris with widespread oral erosions?"
Options: [
  "Topical agents cannot achieve sufficient mucosal concentration to suppress the autoimmune response systemically",
  "Topical corticosteroids are contraindicated in the presence of oral erosions",
  "Systemic therapy is less expensive than topical formulations",
  "Topical corticosteroids cause more candidal superinfection than systemic therapy"
]
Answer: "A"

Open-Ended Template - D6 Expert:
Question: "Explain the rationale for using steroid-sparing immunosuppressants (e.g., azathioprine, mycophenolate mofetil) in the long-term management of oral pemphigus vulgaris, including the mechanism by which they reduce disease activity and the risks they mitigate compared to prolonged corticosteroid monotherapy."
Answer: "Steroid-sparing agents are introduced to reduce cumulative corticosteroid exposure, which causes osteoporosis, adrenal suppression, diabetes, and immunosuppression-related infections. Azathioprine inhibits purine synthesis, suppressing lymphocyte proliferation..."
```

---

## Difficulty Calibration

| Level | Criteria | Example Cognitive Demand |
|-------|----------|------------------------|
| easy | Explain a single, well-established mechanism or distinguish two clearly different conditions | "Why does fluoride prevent caries?" |
| medium | Compare 2 related concepts, explain a multi-step mechanism, or differentiate conditions with overlapping features | "Contrast the pathogenesis of OLP vs. lichenoid reaction" |
| hard | Multi-factor reasoning across pathology/pharmacology/immunology; atypical presentations in differential | "Explain why erosive OLP may mimic pemphigus clinically and how histology resolves the distinction" |
| expert | Novel or evolving concepts; conflicting evidence; requires integrating recent literature with established mechanisms | "Evaluate the proposed role of Th17 cytokines in OLP pathogenesis and its therapeutic implications" |

---

## Generation Process

1. Select a dimension (D4, D5, or D6) and subspecialty.
2. Identify a source that explains a mechanism, differential, or treatment rationale.
3. If the source is an exam question, extract the underlying reasoning concept and create an original English item testing that reasoning. Do NOT translate or copy the source question.
4. Formulate a question that requires reasoning. Test by asking: "Can this be answered by recalling a single fact?" If yes, revise or reclassify to Factual.
5. For MC: ensure distractors represent plausible alternative reasoning paths, not obviously wrong facts.
6. For open-ended: the reference_answer must trace the reasoning chain, not just state the conclusion.
7. Assign difficulty using the calibration table.
8. Fill `source_reference` and `evaluation_criteria`.

---

## Constraints

- Do NOT write questions that can be answered by memorizing a single fact. Every item must require at least one reasoning step.
- Do NOT use "All of the above" or "None of the above."
- Do NOT generate questions answerable by common sense alone.
- Do NOT create differential diagnosis questions where only one option is a real disease.
- Do NOT use case reports as source material for any conceptual item.
- Do NOT set `source_type` to `"case_report"` or `"web"` on any conceptual item.
- For D5 items, always present at least 2 genuinely plausible differential diagnoses in the stem or options.
- For D6 items, the question must ask why a treatment is chosen, not merely what treatment to give.
- For D4 items, the question must ask about a process or mechanism, not merely name a pathological finding.
- Each question must be self-contained. Do NOT reference external figures or tables.
- Do NOT reference the source document in the question text. No "According to...", "Based on the guideline...", "The book states...".
- Do NOT ask about "advances", "overview", "recent developments", or "trends". Ask about specific mechanisms, differentials, or rationale.
- Use current nomenclature and classification systems.

## Dimension Boundary Rules (CRITICAL)

Before assigning a dimension, apply these tests:

1. Does the question ask WHY or HOW a disease occurs (pathogenesis, etiology, molecular mechanism)? → **D4.** If it only asks WHAT the features are, that is D2 Factual, not D4.

2. Does the question ask to DISTINGUISH or COMPARE 2+ conditions? → **D5.** There must be at least 2 conditions being compared.

3. Does the question ask WHY a specific treatment is chosen over alternatives? → **D6.** If it only asks WHAT treatment to give, that is D7 Procedural.

4. Does the question ask about a drug mechanism of action or material property? → Even if reasoning is involved, if the core is about the drug/material itself, consider D3 Factual instead.

Examples of WRONG dimension assignment:
- "What are the clinical features of periodontitis?" → This is D2 Factual (recall), NOT D4 Conceptual
- "Classify this Kennedy classification" → This is D2 Factual (classification recall), NOT D4 Conceptual
- "What treatment is recommended for X?" → This is D7 Procedural (clinical decision), NOT D6 Conceptual
- "Explain the mechanism of action of chlorhexidine" → This is D3 Factual (drug knowledge), NOT D4 Conceptual

## Open-Ended Question Stem Rules (CRITICAL)

For open-ended items, the question stem must be CONCISE and must NOT pre-list the answer points.

BAD (over-prompted — gives away the answer structure):
"Explain the pathophysiological mechanisms by which intraoral galvanic currents and thermal conduction can produce dentin hypersensitivity and mucosal irritation. Include the roles of saliva, dissimilar metal potentials, dentinal fluid dynamics, and possible immune-mediated reactions."

GOOD (concise — lets the model demonstrate its own reasoning):
"A patient reports sharp pain when a new metallic restoration contacts an opposing gold crown. Explain the likely mechanism."

Rules:
- Do NOT list specific mechanisms, pathways, or factors the answer should cover.
- Do NOT use "Include the roles of...", "Discuss the following aspects...", "Address X, Y, and Z...".
- Do NOT use "Explain... by which..." followed by the answer.
- The question should state the clinical scenario or concept, then ask a single open question.
- Keep question stems under 2 sentences for open-ended items.
- The reference_answer should contain the detailed points — NOT the question stem.
