---
name: qa-procedural
description: >
  Generate Level 3 (Procedural) knowledge QA items covering D7 (Clinical Decision & Planning)
  and D8 (Multidisciplinary Case Analysis), presenting clinical scenarios that require
  multi-step diagnostic and treatment reasoning. Use when populating the benchmark with
  case-based items that test clinical decision-making and MDT coordination.
metadata:
  author: OralBench Team
  version: "1.1"
---

# QA Procedural Generation

## Scope

Generate QA items for knowledge_type `"Procedural"` across two dimensions:

| Dimension | Code | Focus |
|-----------|------|-------|
| Clinical Decision & Planning | D7 | Diagnosis from clinical scenario, recommended examinations, treatment planning, complication management |
| Multidisciplinary Case Analysis | D8 | Complex cases requiring coordination across oral medicine, surgery, oncology, internal medicine, or other specialties |

Every item must present a clinical scenario requiring multi-step reasoning. Do NOT write cases with obvious single-step answers.

---

## Source Material

Valid sources for Procedural items are:

1. **Exam questions** (Chinese dental licensing exams and similar structured exam banks)
2. **PDF sources** (textbooks and clinical guidelines)
3. **Case reports** (published clinical case reports)

When source is exam questions (Chinese dental licensing), use them as INSPIRATION for clinical scenarios. Extract the clinical decision-making concept and build an original English case scenario around it. Do NOT translate verbatim. Do NOT copy question stems, option lists, or answer explanations from the source exam.

When source is case reports, use real case presentations to create clinical decision questions. Extract the clinical scenario, decision points, and management challenges. Reconstruct as an original item — do NOT reproduce the case report verbatim.

When source is PDF (textbooks or guidelines), use treatment protocols and guidelines for planning questions. Identify the multi-step clinical protocol and build a scenario that tests the decision-making pathway.

---

## Output Schema Requirements

Set these fields on every generated item:

- `knowledge_type`: `"Procedural"`
- `dimension`: `"D7"` or `"D8"`
- `question_format`: `"multiple-choice"` or `"open-ended"`
- `difficulty`: `"medium"`, `"hard"`, or `"expert"` (do NOT assign `"easy"` to any Procedural item)
- `subspecialty`: one or more values from the `Subspecialty` enum
- `source_type`: `"textbook"`, `"guideline"`, `"exam"`, or `"case_report"`
- `source_reference`: must include `title` and at least one of `doi_or_url` or `page_or_section`
- `language`: `"en"`

---

## Case Scenario Template

Every procedural item must include a structured clinical scenario. Use this template for the case presentation embedded in the `question` field:

```
Demographics: [age], [sex], [relevant medical history summary]
Chief complaint: [primary reason for visit]
History of present illness: [onset, duration, progression, associated symptoms, prior treatments]
Medical history: [systemic conditions, medications, allergies]
Examination findings: [extraoral and intraoral findings, vital signs if relevant]
Available test results: [radiographic findings, lab values, biopsy results — include only what is available at the point of the question]
```

Do NOT provide all information upfront if the question asks what additional workup to order. Present only the information available at the decision point.

---

## Format Rules

### Multiple-Choice

- Exactly 4 options (A-D), exactly one correct.
- Options must represent distinct clinical management paths, not trivially wrong choices.
- Do NOT use "All of the above" or "None of the above."
- Each distractor must be a defensible clinical choice that is suboptimal for the specific scenario, not an absurd action.

### Open-Ended

- `question`: the full case scenario followed by a specific clinical question.
- `options`: `[]`
- `answer`: concise management plan (3-5 sentences).
- `reference_answer`: comprehensive answer (5-12 sentences) with step-by-step reasoning, including what to do first, what to order, and why.
- `explanation`: common management errors and why the chosen approach is preferred.

---

## Question Templates by Dimension

### D7: Clinical Decision & Planning

Present a clinical scenario and ask for diagnosis, recommended examinations, or treatment plan.

```
MC Template - D7 Medium:
Question: "A 55-year-old male smoker presents with a painless, indurated ulcer on the right lateral tongue, 1.5 cm in diameter, present for 6 weeks. No cervical lymphadenopathy is palpable. What is the most appropriate next step?"
Options: [
  "Prescribe a 2-week course of antibiotics and reassess",
  "Perform an incisional biopsy of the ulcer margin",
  "Apply toluidine blue staining and photograph for monitoring",
  "Order a PET-CT scan to evaluate for distant metastasis"
]
Answer: "B"

Open-Ended Template - D7 Hard:
Question: "Demographics: 62-year-old female. Chief complaint: persistent burning sensation of the tongue for 4 months. Medical history: type 2 diabetes (HbA1c 8.2%), hypertension, taking metformin and lisinopril. Examination findings: erythematous, atrophic tongue dorsum with loss of filiform papillae; angular cheilitis bilaterally. Available test results: none yet obtained.

Outline your diagnostic workup and differential diagnosis. For each differential, state what test result would confirm or exclude it."
Answer: "The differential includes iron deficiency anemia, vitamin B12/folate deficiency, oral candidiasis, and burning mouth syndrome. Initial workup: CBC with differential, serum ferritin, vitamin B12, folate, fasting glucose (already known elevated), and oral swab for Candida culture..."
```

### D8: Multidisciplinary Case Analysis

Present a complex case involving multiple specialties and ask for an MDT approach.

```
MC Template - D8 Expert:
Question: "A 68-year-old male with a 3-year history of IV bisphosphonate therapy for multiple myeloma presents with exposed necrotic bone in the left posterior mandible following extraction of tooth #36 eight weeks ago. CT shows osteolysis extending to the inferior border. He is currently on chemotherapy (bortezomib + dexamethasone). His oncologist reports stable disease. Which multidisciplinary management approach is most appropriate?"
Options: [
  "Immediate segmental mandibulectomy with free fibula flap reconstruction",
  "Conservative debridement, antimicrobial rinses, systemic antibiotics, and coordination with oncology regarding bisphosphonate drug holiday",
  "Hyperbaric oxygen therapy followed by sequestrectomy",
  "Discontinue all bisphosphonate therapy permanently and observe for spontaneous bone healing"
]
Answer: "B"

Open-Ended Template - D8 Expert:
Question: "Demographics: 45-year-old female. Chief complaint: progressive difficulty opening mouth over 3 months. Medical history: systemic sclerosis (diffuse cutaneous type) diagnosed 5 years ago, Raynaud phenomenon, esophageal dysmotility, on mycophenolate mofetil and low-dose prednisone. Examination findings: maximum interincisal opening 18 mm, microstomia, perioral skin tightening with loss of lip vermilion, generalized gingival recession, xerostomia. Available test results: panoramic radiograph shows widened PDL spaces bilaterally, no bony pathology.

This patient requires coordinated care across multiple specialties. Identify the relevant specialties, outline each specialty's role, and propose an integrated management plan addressing both the oral and systemic aspects."
Answer: "Relevant specialties: oral medicine, rheumatology, physiotherapy/occupational therapy, periodontology, prosthodontics. Oral medicine: manage xerostomia (saliva substitutes, pilocarpine if not contraindicated), monitor for oral mucosal changes. Rheumatology: optimize systemic sclerosis management, assess whether immunosuppressive regimen adjustment could slow fibrosis progression. Physiotherapy: jaw stretching exercises (e.g., TheraBite) to maintain/improve mouth opening. Periodontology: aggressive preventive care given xerostomia and recession. Prosthodontics: consider sectional dentures or modified prostheses accommodating limited opening..."
```

---

## Difficulty Calibration

Do NOT assign "easy" to any Procedural item.

| Level | Criteria | Case Complexity |
|-------|----------|----------------|
| medium | Standard clinical protocol; single complication; straightforward diagnostic pathway | Classic presentation, 2-3 step management |
| hard | Complex multi-step management; atypical presentation; complication requiring protocol deviation | Comorbidities affecting treatment, conflicting findings |
| expert | MDT coordination with conflicting priorities; rare conditions; systemic-oral interaction requiring specialist input from 3+ fields | Multiple active conditions, immunocompromised host, treatment trade-offs |

---

## Generation Process

1. Select D7 or D8 and one or more subspecialties.
2. Identify a source: exam question, case report, or textbook/guideline protocol.
3. If the source is an exam question, extract the clinical decision concept and build an original English case scenario. Do NOT translate or copy the source.
4. If the source is a case report, extract the clinical scenario and decision points. Reconstruct as an original item.
5. If the source is a guideline/textbook, identify the multi-step protocol and build a scenario testing that pathway.
6. Construct a clinical scenario using the case template. Include enough detail for multi-step reasoning.
7. Formulate a question that requires a management decision, not a single-fact answer.
8. For D8: ensure the case genuinely requires input from at least 2 specialties. Name the specialties and their roles.
9. For MC: make every distractor a defensible but suboptimal clinical action.
10. Assign difficulty (medium, hard, or expert only).
11. Fill `source_reference` and `evaluation_criteria`.

---

## Constraints

- Do NOT assign difficulty "easy" to any Procedural item.
- Do NOT write cases with obvious single-step answers. Every case must require multi-step reasoning.
- Do NOT present all diagnostic information upfront when the question asks what workup to order.
- Do NOT create MC distractors that are absurd or clearly non-clinical actions.
- Do NOT write D8 items that can be managed by a single specialty. If only one specialty is needed, reclassify to D7.
- Do NOT use "All of the above" or "None of the above."
- Do NOT set `source_type` to `"web"` on any procedural item.
- Do NOT reference the source document in the question text. No "According to...", "Based on the guideline...", "The case report describes...".
- Do NOT ask about "advances", "overview", or "trends". Present concrete clinical scenarios.
- Ensure patient demographics are realistic and clinically relevant (age, sex, medical history affect management).
- Include medication names with generic (INN) names, not brand names.
- All clinical values (lab results, measurements) must be realistic and internally consistent.
- Each case must be self-contained. Do NOT reference external images or prior cases.

## Dimension Boundary Rules (CRITICAL)

D7 vs D8 distinction:
- **D7 (Clinical Decision & Planning)**: A single clinician can manage the case. Requires diagnosis + workup + treatment plan.
- **D8 (Multidisciplinary Case)**: The case REQUIRES coordination across 2+ specialties (e.g., orthodontics + surgery, periodontics + prosthodontics + implantology). If only one specialty is needed, it is D7.

D7 vs D6 distinction:
- **D6 (Treatment Rationale, Conceptual)**: Asks WHY a treatment is chosen — justification of the decision.
- **D7 (Clinical Decision, Procedural)**: Asks WHAT to do — the full management plan for a clinical scenario.

Examples of WRONG assignment:
- "Why is extraction preferred over root canal for this tooth?" → D6 Conceptual (asks WHY), NOT D7
- "A patient presents with X. What is your diagnosis and treatment plan?" → D7 Procedural (asks WHAT to do)
- "A patient needs orthodontics and orthognathic surgery. Plan the treatment." → D8 (requires 2+ specialties)

## Open-Ended Question Stem Rules (CRITICAL)

For open-ended procedural items, present the clinical scenario concisely, then ask a single open question. Do NOT pre-list what the answer should cover.

BAD (over-prompted):
"A 45-year-old presents with a swelling. Provide your diagnosis, differential diagnosis, recommended imaging, biopsy approach, and treatment plan including surgical margins and reconstruction options."

GOOD (concise):
"A 45-year-old presents with a firm, painless swelling in the left posterior mandible. Panoramic radiograph shows a multilocular radiolucency. How would you manage this patient?"

Rules:
- Present the clinical scenario with relevant findings (demographics, chief complaint, exam findings, test results).
- Ask ONE open question: "How would you manage this patient?", "What is your approach?", "Outline your management plan."
- Do NOT list specific steps the answer should include (e.g., "Include diagnosis, imaging, biopsy, treatment, follow-up").
- Do NOT use "Discuss the following aspects..." or "Address X, Y, and Z...".
- Keep the question portion (after the scenario) to ONE sentence.
- The reference_answer should contain the comprehensive management plan — NOT the question stem.
