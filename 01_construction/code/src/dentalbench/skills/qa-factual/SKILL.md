---
name: qa-factual
description: >
  Generate Level 1 (Factual) knowledge QA items covering D1 (Anatomy & Physiology),
  D2 (Disease Characteristics), and D3 (Materials & Pharmacology) in multiple-choice
  and open-ended formats. Use when populating the benchmark with single-fact-recall
  items across these three dimensions.
metadata:
  author: OralBench Team
  version: "2.1"
---

# QA Factual Generation

## Scope

Generate QA items for knowledge_type `"Factual"` across three dimensions:

| Dimension | Code | Focus |
|-----------|------|-------|
| Anatomy & Physiology | D1 | Structures, innervation, blood supply, histology, developmental biology, normal function |
| Disease Characteristics | D2 | Epidemiology, clinical features, classification systems, diagnostic criteria, pathognomonic signs |
| Materials & Pharmacology | D3 | Dental material properties, drug names/classes/dosages, mechanisms of action, contraindications |

Target distribution: D1 ~35%, D2 ~40%, D3 ~25% of all factual items.
Target format split: ~60% multiple-choice, ~40% open-ended.

---

## Source Material

Valid sources for Factual items are:

1. **Exam questions** (Chinese dental licensing exams and similar structured exam banks)
2. **PDF sources** (textbooks and clinical guidelines)

When source is exam questions (Chinese dental licensing), use them as INSPIRATION to create original English questions testing the same concepts. Do NOT translate verbatim. Do NOT copy question stems, option lists, or answer explanations from the source exam. Reconstruct the tested concept as a new, original English-language item.

When source is PDF (textbooks or guidelines), extract the factual claim, verify it against the source, and formulate an original question around it.

Do NOT use case reports as source for factual items. Case reports belong to L3/L4 generation only.

---

## Output Schema Requirements

Set these fields on every generated item:

- `knowledge_type`: `"Factual"`
- `dimension`: `"D1"`, `"D2"`, or `"D3"`
- `question_format`: `"multiple-choice"` or `"open-ended"`
- `difficulty`: `"easy"`, `"medium"`, `"hard"`, or `"expert"`
- `subspecialty`: one or more values from the `Subspecialty` enum
- `source_type`: `"textbook"`, `"guideline"`, or `"exam"`
- `source_reference`: must include `title` and at least one of `doi_or_url` or `page_or_section`
- `language`: `"en"`

---

## Multiple-Choice Format Rules

- Provide exactly 4 options labeled A through D.
- Set exactly one correct answer.
- Store the correct letter in `answer` (e.g., `"B"`).
- Store option texts in `options` as an array of 4 strings without letter prefixes.
- Make all distractors plausible and from the same domain.
- Do NOT use "All of the above" or "None of the above" as options.
- Do NOT use negative stems ("Which is NOT...") for easy-difficulty items. Permit negative stems only at hard and expert levels.
- Do NOT make the correct option consistently longer than distractors.
- Ensure every option is grammatically consistent with the stem.
- Do NOT create overlapping options where one subsumes another.

## Open-Ended Format Rules

- Store a direct question or fill-in-the-blank prompt in `question`.
- Set `options` to `[]`.
- Store a concise correct answer (1-3 sentences) in `answer`.
- Store a comprehensive answer (3-8 sentences) with supporting detail in `reference_answer`.
- Store why the answer is correct and what common errors exist in `explanation`.

---

## Question Templates by Dimension

### D1: Anatomy & Physiology

Topics: tooth morphology, numbering systems (FDI/Universal/Palmer), oral and maxillofacial anatomy, muscles of mastication, TMJ, salivary glands, nerve pathways, histology of oral tissues, embryological development, physiology of saliva/mastication/swallowing, blood supply, lymphatic drainage, innervation patterns.

```
MC Template - D1 Easy:
Question: "Which branch of the trigeminal nerve provides sensory innervation to the lower teeth?"
Options: ["Ophthalmic (V1)", "Maxillary (V2)", "Inferior alveolar nerve (V3)", "Buccal nerve"]
Answer: "C"

MC Template - D1 Hard:
Question: "The cell-rich zone of the dental pulp is located immediately subjacent to which layer?"
Options: ["Odontoblast layer", "Cell-free zone of Weil", "Pulp core", "Predentin"]
Answer: "B"

Open-Ended Template - D1 Medium:
Question: "Describe the arterial blood supply to the mandible, including the primary and secondary sources."
Answer: "The inferior alveolar artery, a branch of the maxillary artery, is the primary blood supply..."
```

### D2: Disease Characteristics

Topics: oral mucosal diseases (aphthous stomatitis, lichen planus, pemphigus, pemphigoid, leukoplakia, erythroplakia), dental caries classification, periodontal diseases (staging/grading), oral infections, oral manifestations of systemic diseases, odontogenic/non-odontogenic cysts and tumors (WHO classification), TMJ disorders, salivary gland diseases, potentially malignant disorders, OSCC.

```
MC Template - D2 Medium:
Question: "Which clinical feature most reliably distinguishes erythroplakia from erythematous candidiasis?"
Options: ["Response to antifungal therapy", "Location on the palate", "Presence of pain", "Patient age over 60"]
Answer: "A"

Open-Ended Template - D2 Hard:
Question: "List the WHO (2022) diagnostic criteria for oral lichen planus and explain how it is distinguished from oral lichenoid lesions."
Answer: "The WHO criteria require bilateral, symmetrical white striations (Wickham striae)..."
```

### D3: Materials & Pharmacology

Topics: restorative materials (composites, GIC, amalgam, ceramics), impression materials, cements, implant materials, local anesthetics (lidocaine, articaine, mepivacaine), analgesics/anti-inflammatories, antibiotics in dentistry, antiseptics, conscious sedation agents.

```
MC Template - D3 Easy:
Question: "What is the maximum recommended dose of lidocaine with epinephrine for a healthy adult?"
Options: ["3.2 mg/kg", "4.4 mg/kg", "7.0 mg/kg", "6.6 mg/kg"]
Answer: "C"

MC Template - D3 Expert:
Question: "Which property of a dental ceramic is most directly improved by the addition of leucite crystals to a feldspathic matrix?"
Options: ["Flexural strength via crack deflection", "Translucency via refractive index matching", "Coefficient of thermal expansion matching to metal substructure", "Chemical solubility resistance"]
Answer: "A"

Open-Ended Template - D3 Medium:
Question: "Explain the setting reaction of glass ionomer cement and the role of polyacrylic acid in the process."
Answer: "Glass ionomer cement sets through an acid-base reaction between fluoroaluminosilicate glass powder and polyacrylic acid..."
```

---

## Difficulty Calibration

| Level | Criteria | Distractor Profile | Target Audience |
|-------|----------|-------------------|-----------------|
| easy | Single fact recall; basic terminology or widely taught definition | From different categories; clearly distinguishable | 2nd-year dental student |
| medium | 2-3 related facts; specific details from standard references | Same category; require discrimination | Clinical-rotation student |
| hard | Uncommon facts, classification details, numerical values; negative stems permitted | Closely related; represent common errors | Recent graduate / resident |
| expert | Rare conditions, advanced material science, subspecialty-level pharmacology | Correct in a different context; nuanced distinctions | Specialist |

---

## Generation Process

1. Select a dimension (D1, D2, or D3) and subspecialty.
2. Identify a source passage from extracted textbook content, clinical guidelines, or exam banks.
3. If the source is an exam question, extract the underlying concept and create an original English item testing that concept. Do NOT translate or copy the source question.
4. Formulate the question stem. Ensure it tests a single, discrete fact.
5. For MC: generate the correct answer and three plausible distractors. Verify exactly one option is unambiguously correct.
6. For open-ended: write the concise answer, the reference answer, and the explanation.
7. Assign difficulty using the calibration table above.
8. Fill `source_reference` with the exact source, page, or DOI.
9. Fill `evaluation_criteria` with `factuality`, `completeness`, and `key_points`.

---

## Constraints

- Every question must be answerable from a single, citable source. Do NOT generate questions requiring synthesis across multiple sources (that belongs to L2 Conceptual).
- Do NOT generate questions answerable by common sense alone.
- Do NOT test trivial or outdated facts unless clinically relevant.
- Do NOT copy verbatim from source material. Paraphrase while preserving accuracy.
- Do NOT use case reports as source material for any factual item.
- Do NOT set `source_type` to `"case_report"` or `"web"` on any factual item.
- Each question must be self-contained. Do NOT reference figures, tables, or "the passage above."
- Do NOT reference the source document in the question text. No "According to the textbook...", "Based on the guideline...", "The book states...". The question must stand alone.
- Do NOT ask about "advances", "overview", "recent developments", or "trends" in a field. Ask about specific clinical facts.
- Use current WHO, AAP/EFP, and ADA classifications. Verify against the most recent edition.
- Double-check all numerical values (doses, concentrations, measurements) against authoritative references.
- Ensure balanced coverage across subspecialties. Track generation counts per subspecialty and dimension.

## Dimension Boundary Rules (CRITICAL)

Before assigning a dimension, apply these tests:

1. Does the question ask about a DRUG (name, dose, mechanism, interaction, contraindication) or a MATERIAL (property, composition, setting reaction, handling)? → **D3, always.** Even if the question mentions a disease context, if the core knowledge tested is about the drug/material, it is D3.

2. Does the question ask about disease features (signs, symptoms, classification, staging, epidemiology, diagnostic criteria)? → **D2.** But only if it asks WHAT the features are, not WHY they occur (that would be D4 Conceptual).

3. Does the question ask about anatomy, histology, embryology, physiology, innervation, blood supply, tooth morphology? → **D1.**

Examples of WRONG dimension assignment:
- "Which component of MTA is responsible for its biocompatibility?" → This is D3 (material), NOT D1
- "What is the drug of choice for dental abscess?" → This is D3 (pharmacology), NOT D2
- "Devitalizing paste typically contains which agent?" → This is D3 (material/drug), NOT D2
- "Why does diabetes increase periodontal risk?" → This is D4 Conceptual (mechanism), NOT D2 Factual
