---
name: qa-metacognitive
description: >
  Generate Level 4 (Metacognitive) knowledge QA items covering D9 (Cognitive Monitoring
  & Uncertainty) and D10 (Reasoning Reflection & Critical Thinking), testing confidence
  calibration, bias identification, evidence appraisal, and self-correction. Use when
  populating the benchmark with items that assess an AI model's ability to reason about
  its own reasoning and recognize the limits of its knowledge.
metadata:
  author: OralBench Team
  version: "1.1"
---

# QA Metacognitive Generation

## Scope

Generate QA items for knowledge_type `"Metacognitive"` across two dimensions:

| Dimension | Code | Focus |
|-----------|------|-------|
| Cognitive Monitoring & Uncertainty | D9 | Confidence calibration, knowledge boundary identification, information gap recognition, uncertainty quantification |
| Reasoning Reflection & Critical Thinking | D10 | Chain-of-thought quality analysis, cognitive bias identification, evidence quality assessment, self-correction under new information |

Every item must require reflection on reasoning processes. If a question has a single correct factual answer without requiring metacognitive awareness, it belongs in another knowledge level.

---

## Source Material

Valid sources for Metacognitive items are:

1. **PDF sources** (textbooks and clinical guidelines)
2. **Case reports** (published clinical case reports)

When source is case reports, use real clinical cases to create uncertainty/reflection scenarios. Extract the diagnostic ambiguity, management dilemmas, or evolving clinical picture and build metacognitive items around those decision points. Do NOT reproduce the case report verbatim.

When source is PDF (textbooks or guidelines), use guideline recommendations to create evidence appraisal tasks. Identify areas where evidence is limited, conflicting, or evolving, and build items that test the model's ability to recognize uncertainty and evaluate evidence quality.

Do NOT use exam questions as source for metacognitive items — exam format is too structured for metacognitive assessment. Exam questions test recall and application, not reflection on reasoning quality or uncertainty calibration.

---

## Output Schema Requirements

Set these fields on every generated item:

- `knowledge_type`: `"Metacognitive"`
- `dimension`: `"D9"` or `"D10"`
- `question_format`: `"metacognitive-open"` or `"metacognitive-analysis"`
- `difficulty`: `"hard"` or `"expert"` (do NOT assign `"easy"` or `"medium"` to any Metacognitive item)
- `subspecialty`: one or more values from the `Subspecialty` enum
- `source_type`: `"textbook"`, `"guideline"`, or `"case_report"`
- `source_reference`: must include `title` and at least one of `doi_or_url` or `page_or_section`
- `language`: `"en"`

---

## Question Format Types

### metacognitive-open

The model generates a metacognitive response: it answers a clinical question AND reflects on its own confidence, uncertainty, or reasoning quality.

Expected response structure:
```
1. ANSWER: [clinical answer]
2. CONFIDENCE: [percentage 0-100% with justification]
3. LIMITATIONS: [knowledge gaps, uncertainties]
4. ALTERNATIVE PERSPECTIVES: [other interpretations considered]
```

### metacognitive-analysis

The model analyzes a given piece of reasoning (a flawed chain-of-thought, a diagnostic rationale, or an evidence summary) and identifies errors, biases, or quality issues.

Expected response structure:
```
1. ANALYSIS: [evaluation of the provided reasoning]
2. ERRORS IDENTIFIED: [specific flaws with explanations]
3. CORRECTED REASONING: [how the reasoning should proceed]
4. DECISION RATIONALE: [why the corrections matter clinically]
```

---

## Question Templates by Dimension

### D9: Cognitive Monitoring & Uncertainty

#### Confidence Calibration Task

```
metacognitive-open Template - D9 Hard:
Question: "A 40-year-old patient presents with a solitary, painless, dome-shaped nodule on the hard palate, 1 cm in diameter, firm on palpation, with intact overlying mucosa. The lesion has been present for approximately 6 months and is slowly growing. Provide your most likely diagnosis, your differential diagnosis, and assign a confidence level (0-100%) to your top diagnosis. Explain what specific findings increase or decrease your confidence."
reference_answer: "The most likely diagnosis is pleomorphic adenoma (mixed tumor) of a minor salivary gland, given the location (hard palate is the most common intraoral site for minor salivary gland tumors), the slow growth, firm consistency, and intact overlying mucosa. Differential includes mucoepidermoid carcinoma, adenoid cystic carcinoma, palatal abscess, and torus palatinus. Confidence ~65-75%: the classic presentation supports pleomorphic adenoma, but the inability to distinguish benign from malignant salivary gland tumors clinically without biopsy limits confidence. Factors increasing confidence: slow growth, intact mucosa, dome shape. Factors decreasing confidence: cannot rule out low-grade mucoepidermoid carcinoma which may present identically."
```

#### Knowledge Boundary Identification

```
metacognitive-open Template - D9 Expert:
Question: "You are asked whether long-term use of topical tacrolimus (0.1%) for erosive oral lichen planus increases the risk of oral malignancy. Provide your assessment, explicitly identify what you know with confidence, what you are uncertain about, and what information gaps exist in the current evidence base."
reference_answer: "Known with confidence: tacrolimus is a calcineurin inhibitor that suppresses local T-cell-mediated inflammation; it is effective for steroid-resistant erosive OLP. Uncertain: the FDA black box warning for topical calcineurin inhibitors is based on theoretical risk and systemic immunosuppression data, not oral-specific evidence. The few long-term studies of oral tacrolimus use (mostly case series, <100 patients, <5 years follow-up) have not demonstrated increased malignancy risk, but are underpowered to detect rare events. Information gaps: no RCTs with malignancy as a primary endpoint; no studies >10 years; confounded by the fact that erosive OLP itself carries a 1-2% malignant transformation risk."
```

#### Information Gap Identification

```
metacognitive-open Template - D9 Hard:
Question: "A 28-year-old female presents with recurrent oral ulcers (3-4 episodes per year), each lasting 10-14 days. She has no genital ulcers, no ocular symptoms, and no skin lesions. Her CBC and inflammatory markers are normal. She asks whether she might have Behcet disease. Identify what information is sufficient to address her concern, what additional information you would need, and what the limits of clinical certainty are in this scenario."
reference_answer: "Sufficient information: recurrent oral ulcers are the most common manifestation of Behcet disease but are also the hallmark of recurrent aphthous stomatitis (RAS), which is far more prevalent. The absence of genital ulcers, ocular involvement, and skin lesions makes Behcet less likely by ISG criteria (requires oral ulcers plus 2 of 4 other criteria). Additional information needed: pathergy test result, HLA-B51 status (supportive but not diagnostic), detailed family history, and whether ulcers leave scars (major aphthae). Limits of certainty: Behcet disease cannot be definitively excluded because systemic manifestations may develop years after oral ulcer onset; no single diagnostic test exists."
```

### D10: Reasoning Reflection & Critical Thinking

#### Chain-of-Thought Quality Analysis

```
metacognitive-analysis Template - D10 Expert:
Question: "A clinician presented the following reasoning about a patient with a white patch on the buccal mucosa:

'The patient has a white patch that cannot be scraped off. This rules out candidiasis. The patch is unilateral and located on the buccal mucosa near a sharp tooth cusp. Since it is white and cannot be scraped off, it is leukoplakia. Leukoplakia has a 5% malignant transformation rate, so I will perform an incisional biopsy.'

Analyze this reasoning chain. Identify any logical errors, missing steps, premature conclusions, or cognitive biases. Provide a corrected reasoning pathway."
reference_answer: "Errors identified: (1) Non-scrapability does not rule out all forms of candidiasis — chronic hyperplastic candidiasis (candidal leukoplakia) also cannot be scraped off. (2) The proximity to a sharp cusp raises frictional keratosis as a differential, which was not considered. (3) Jumping to 'leukoplakia' without considering other white lesions (lichen planus, white sponge nevus, leukoedema) represents premature closure bias. (4) The 5% malignant transformation rate is a rough population average and varies significantly by subtype, location, and presence of dysplasia — citing it as justification for biopsy without considering these factors is an anchoring bias. Corrected reasoning: (1) Eliminate frictional cause by smoothing the sharp cusp and reassessing in 2-3 weeks. (2) If the lesion persists, consider the full differential of non-scrapable white lesions. (3) Perform biopsy with the specific goal of assessing for dysplasia, not just confirming 'leukoplakia.'"
```

#### Cognitive Bias Identification

```
metacognitive-analysis Template - D10 Hard:
Question: "A dentist sees three patients in one morning with oral ulcers, all of whom are diagnosed with recurrent aphthous stomatitis. The fourth patient presents with a single, persistent ulcer on the ventral tongue present for 5 weeks. The dentist diagnoses aphthous stomatitis and prescribes topical corticosteroids with a 2-week follow-up. Identify the cognitive bias at play, explain why it is dangerous in this context, and describe what the clinician should have done differently."
reference_answer: "The cognitive bias is availability bias (also called frequency bias) — the clinician's recent experience with multiple aphthous stomatitis cases made that diagnosis more cognitively accessible, leading to premature pattern matching. This is dangerous because a single, persistent ulcer on the ventral tongue lasting 5 weeks is a red flag for oral squamous cell carcinoma or other malignancy. Aphthous ulcers typically heal within 1-2 weeks (minor) or 6 weeks (major, but usually with a history of recurrence). The clinician should have: (1) noted the atypical features (single, persistent, ventral tongue location), (2) generated a broader differential including malignancy, traumatic ulcerative granuloma, and chronic infection, (3) performed or referred for incisional biopsy given the >3-week duration."
```

#### Self-Correction Task

```
metacognitive-open Template - D10 Expert:
Question: "Initial information: A 60-year-old male presents with bilateral parotid gland enlargement. He has a history of chronic alcohol use. You are asked for your initial differential diagnosis.

[After you provide your initial assessment, consider this additional information]: Serological testing reveals anti-SSA/Ro and anti-SSB/La antibodies. Schirmer test shows <5 mm wetting in 5 minutes bilaterally. Minor salivary gland biopsy shows focal lymphocytic sialadenitis with a focus score >1.

Revise your diagnosis. Explain what changed in your reasoning, what initial assumptions were incorrect, and how the new evidence shifted your differential."
reference_answer: "Initial assessment likely prioritized alcohol-related sialadenosis (most common cause of bilateral parotid enlargement in a male with alcohol history), with differentials including sarcoidosis, lymphoma, and Sjogren syndrome. After new information: the positive anti-SSA/Ro, anti-SSB/La, abnormal Schirmer test, and focal lymphocytic sialadenitis with focus score >1 meet the 2016 ACR/EULAR classification criteria for Sjogren syndrome. Reasoning shift: the initial anchoring on alcohol history was a framing bias — the demographic (male, alcohol use) made sialadenosis seem most likely, but Sjogren syndrome, though more common in females, does occur in males. The serological and histological evidence is definitive. Self-correction: the initial differential should have weighted Sjogren syndrome more heavily regardless of sex, because bilateral parotid enlargement is a classic presentation. The alcohol history was a red herring that should have been treated as a comorbidity, not the primary diagnostic anchor."
```

#### Evidence Quality Assessment

```
metacognitive-analysis Template - D10 Expert:
Question: "A colleague cites the following evidence to support using photodynamic therapy (PDT) for erosive oral lichen planus: 'A 2023 systematic review of 8 RCTs (total n=186) found PDT superior to placebo for pain reduction (SMD -1.2, 95% CI -1.8 to -0.6) with no serious adverse events.' Critically appraise this evidence. Identify strengths, weaknesses, and what additional information you would need before recommending PDT to a patient."
reference_answer: "Strengths: systematic review of RCTs is high-level evidence; statistically significant effect size; safety profile appears favorable. Weaknesses: (1) Very small total sample size (n=186 across 8 RCTs, averaging ~23 per trial) — underpowered to detect rare adverse events or small subgroup differences. (2) The wide confidence interval (-1.8 to -0.6) suggests high heterogeneity between studies. (3) No information on follow-up duration — OLP is chronic and relapsing, so short-term pain reduction may not reflect long-term benefit. (4) Comparison to placebo only — no head-to-head comparison with standard topical corticosteroids. (5) Publication bias risk is high with small studies. Additional information needed: heterogeneity statistics (I-squared), PDT protocol details (photosensitizer, wavelength, sessions), outcome measurement tools, follow-up duration, comparison with active treatment, and cost-effectiveness data."
```

---

## Difficulty Calibration

Do NOT assign "easy" or "medium" to any Metacognitive item.

| Level | Criteria | D9 Example | D10 Example |
|-------|----------|-----------|-------------|
| hard | Identify uncertainty in a moderately ambiguous clinical scenario; recognize a single cognitive bias | Confidence calibration for a classic presentation with one atypical feature | Identify availability bias in a diagnostic scenario |
| expert | Quantify uncertainty with nuanced evidence appraisal; identify multiple interacting biases; self-correct under contradictory information; evaluate complex evidence quality | Knowledge boundary mapping for an evolving clinical question with limited evidence | Analyze a multi-step flawed reasoning chain with 3+ errors; appraise a systematic review with methodological limitations |

---

## Generation Process

1. Select D9 or D10 and a subspecialty.
2. Identify a source: case report or textbook/guideline.
3. If the source is a case report, extract the diagnostic ambiguity or management dilemma and build a metacognitive item around it.
4. If the source is a guideline/textbook, identify areas of limited or conflicting evidence and build an evidence appraisal or uncertainty task.
5. Choose a question format: `metacognitive-open` or `metacognitive-analysis`.
6. For D9: construct a clinical scenario with genuine diagnostic uncertainty. For D10: construct a reasoning artifact (flawed CoT, biased rationale, or evidence summary) for the model to analyze.
7. Write the `reference_answer` as a model metacognitive response that demonstrates the target reasoning quality.
8. For self-correction tasks: provide initial information, then contradictory information, and specify that the model must revise.
9. Assign difficulty (hard or expert only).
10. Fill `source_reference` and `evaluation_criteria`.

---

## Constraints

- Do NOT assign "easy" or "medium" to any Metacognitive item.
- Do NOT use exam questions as source material for any metacognitive item. Exam format is too structured for metacognitive assessment.
- Do NOT set `source_type` to `"exam"` or `"web"` on any metacognitive item.
- Do NOT write metacognitive questions that have a single correct factual answer. Every item must require reflection on reasoning, uncertainty, or evidence quality.
- Do NOT create D10 items where the "flawed reasoning" contains only trivially obvious errors. The errors must be subtle enough to require careful analysis.
- Do NOT write confidence calibration tasks where the correct confidence is 0% or 100%. All scenarios must involve genuine uncertainty.
- For self-correction tasks, the contradictory information must be clinically realistic, not fabricated to be impossible.
- For evidence appraisal tasks, use realistic study characteristics (sample sizes, effect sizes, confidence intervals).
- Do NOT use "All of the above" or "None of the above" in any MC-format items.
- Each item must be self-contained. Do NOT reference external figures, tables, or prior items.
- Do NOT reference the source document in the question text. No "According to...", "Based on the guideline...", "The case report describes...".
- Do NOT ask about "advances", "overview", or "trends". Present concrete clinical metacognitive scenarios.
- The `reference_answer` must model the expected metacognitive structure (ANSWER/CONFIDENCE/LIMITATIONS or ANALYSIS/ERRORS/CORRECTED REASONING), not just provide a factual answer.

## Dimension Boundary Rules (CRITICAL)

D9 vs D10 distinction:
- **D9 (Cognitive Monitoring & Uncertainty)**: The question asks the model to ASSESS ITS OWN knowledge state — express confidence, identify what it doesn't know, recognize information gaps, quantify uncertainty. The model must introspect.
- **D10 (Reasoning Reflection & Critical Thinking)**: The question asks the model to ANALYZE A REASONING CHAIN (its own or a given one) — find logical errors, identify cognitive biases, evaluate evidence quality, revise conclusions. The model must critique reasoning.

D9/D10 vs lower levels:
- If the question can be answered with a factual statement without any metacognitive reflection → it belongs in L1-L3, NOT L4.
- If the question asks "what is the diagnosis?" → D7 Procedural. If it asks "how confident are you in this diagnosis and what would change your mind?" → D9 Metacognitive.
- If the question asks "what is the treatment plan?" → D7 Procedural. If it asks "identify the cognitive bias in this clinician's reasoning about the treatment" → D10 Metacognitive.

Examples of WRONG assignment:
- "What is the differential diagnosis for X?" → D5 Conceptual, NOT D9
- "Describe the treatment for Y" → D7 Procedural, NOT D10
- "What are the risk factors for Z?" → D2 Factual, NOT D9

## Open-Ended Question Stem Rules (CRITICAL)

For metacognitive items, present the scenario concisely, then ask a single metacognitive question. Do NOT pre-list what the answer should cover.

BAD (over-prompted):
"Assess your confidence in the diagnosis, identify three sources of uncertainty, explain what additional information would change your assessment, and discuss potential cognitive biases that might affect your reasoning."

GOOD (metacognitive-open, D9):
"A 60-year-old presents with an asymptomatic radiolucency at the apex of a vital tooth. What is your assessment, and how certain are you?"

GOOD (metacognitive-analysis, D10):
"A clinician diagnosed oral lichen planus based solely on clinical appearance without biopsy, reasoning that 'bilateral white striae are pathognomonic.' Evaluate this reasoning."

Rules:
- Present the clinical scenario or reasoning chain concisely.
- Ask ONE metacognitive question — about confidence, uncertainty, bias, or reasoning quality.
- Do NOT list specific aspects to address ("Include confidence level, sources of uncertainty, cognitive biases...").
- Do NOT use "Discuss the following..." or "Address X, Y, and Z...".
- The reference_answer should model the full metacognitive structure — NOT the question stem.
