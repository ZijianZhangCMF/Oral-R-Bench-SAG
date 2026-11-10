---
name: difficulty-calibration
description: >
  Validate and adjust difficulty labels on QA items by applying level-specific criteria
  per knowledge type (Factual, Conceptual, Procedural, Metacognitive). Use after QA
  generation to ensure difficulty labels accurately reflect cognitive demand and to
  enforce constraints such as no "easy" Procedural or Metacognitive items.
metadata:
  author: OralBench Team
  version: "1.0"
---

# Difficulty Calibration

## Scope

Review the `difficulty` label on every QA item and either confirm it or reassign it based on the criteria defined below. Difficulty must reflect the cognitive demand on the target audience, not the rarity of the disease or the length of the question.

---

## Difficulty Criteria by Knowledge Type

### Factual (K1)

| Level | Criteria | Distractor Profile | Target Audience |
|-------|----------|-------------------|-----------------|
| easy | Single fact recall: a name, definition, number, or classification taught in preclinical years | Distractors from different categories; clearly distinguishable | 2nd-year dental student |
| medium | Recall of 2-3 related facts, or a specific detail from standard references requiring discrimination | Distractors from the same category; require careful reading | Clinical-rotation student |
| hard | Uncommon facts, precise numerical values, detailed classification criteria, or tricky distractors that represent common errors; negative stems permitted | Closely related distractors; may include values correct in a different context | Recent graduate / resident |
| expert | Rare conditions, advanced subspecialty knowledge, nuanced material science or pharmacology distinctions | Distractors that are correct in adjacent contexts; require specialist-level discrimination | Specialist |

### Conceptual (K2)

| Level | Criteria | Reasoning Demand |
|-------|----------|-----------------|
| easy | Explain a single, well-established mechanism or distinguish two clearly different conditions | One reasoning step; textbook explanation |
| medium | Compare 2 related concepts, explain a multi-step mechanism, or differentiate conditions with overlapping features | 2-3 reasoning steps; requires integration |
| hard | Multi-factor reasoning across pathology/pharmacology/immunology; atypical presentations in differential diagnosis | 3+ reasoning steps; requires deep domain knowledge |
| expert | Novel or evolving concepts; conflicting evidence; requires integrating recent literature with established mechanisms; evaluate competing hypotheses | Synthesis across multiple domains; no single textbook answer |

### Procedural (K3)

Do NOT assign "easy" to any Procedural item.

| Level | Criteria | Case Complexity |
|-------|----------|----------------|
| medium | Standard clinical protocol; single complication; straightforward diagnostic pathway with a classic presentation | 2-3 step management; one active problem |
| hard | Complex multi-step management; atypical presentation; complication requiring protocol deviation; comorbidities affecting treatment choice | 4+ step management; 2 active problems; conflicting findings |
| expert | MDT coordination with conflicting priorities; rare conditions; systemic-oral interaction requiring specialist input from 3+ fields; treatment trade-offs with no clearly superior option | Multiple active conditions; immunocompromised host; requires weighing risks across specialties |

### Metacognitive (K4)

Do NOT assign "easy" or "medium" to any Metacognitive item.

| Level | Criteria | Metacognitive Demand |
|-------|----------|---------------------|
| hard | Identify uncertainty in a moderately ambiguous scenario; recognize a single cognitive bias; calibrate confidence for a presentation with one atypical feature | Single metacognitive operation (identify bias OR calibrate confidence OR recognize gap) |
| expert | Quantify uncertainty with nuanced evidence appraisal; identify multiple interacting biases; self-correct under contradictory information; evaluate complex evidence with methodological limitations | Multiple metacognitive operations combined; requires reasoning about reasoning at multiple levels |

---

## Calibration Procedure

For each item, execute these steps in order:

1. Read the complete item: question, options (if MC), answer, reference_answer, explanation.
2. Identify the `knowledge_type`. Confirm it matches the item content. If misclassified, flag for reclassification before calibrating difficulty.
3. Count the reasoning steps required to arrive at the correct answer.
4. Assess the specificity of knowledge required: is this taught in preclinical courses, clinical rotations, residency, or fellowship?
5. For MC items: evaluate distractor plausibility. More plausible distractors increase effective difficulty.
6. Match the item against the criteria table for its knowledge type.
7. Assign the difficulty level. If the current label matches, confirm. If not, reassign and document the reason.

---

## Constraint Enforcement

Apply these hard constraints. Violations must be corrected, not just flagged:

- If `knowledge_type` is `"Procedural"` and `difficulty` is `"easy"`: reassign to `"medium"` minimum.
- If `knowledge_type` is `"Metacognitive"` and `difficulty` is `"easy"` or `"medium"`: reassign to `"hard"` minimum.
- If `knowledge_type` is `"Factual"` and the item requires multi-step reasoning: either reclassify the knowledge_type to Conceptual or increase difficulty to hard/expert.
- If `difficulty` is `"expert"` but the item tests a single well-known fact: downgrade to the appropriate level.

---

## Calibration Output Format

For each calibrated item, produce:

```json
{
  "question_id": "OB_D2_OMUC_042",
  "original_difficulty": "medium",
  "calibrated_difficulty": "hard",
  "changed": true,
  "rationale": "Item requires distinguishing 3 clinically similar conditions with overlapping features (OLP, lichenoid reaction, chronic GVHD). Distractors are highly plausible. Meets 'hard' criteria for Conceptual: multi-factor reasoning across immunology and clinical presentation.",
  "reasoning_steps_counted": 3,
  "constraint_violations_fixed": []
}
```

When no change is needed:

```json
{
  "question_id": "OB_D1_ANAT_015",
  "original_difficulty": "easy",
  "calibrated_difficulty": "easy",
  "changed": false,
  "rationale": "Single fact recall (nerve innervation). Distractors are from different nerve branches. Matches 'easy' criteria for Factual.",
  "reasoning_steps_counted": 1,
  "constraint_violations_fixed": []
}
```

---

## Batch Calibration Statistics

After processing all items, produce a summary:

```json
{
  "calibration_summary": {
    "total_items_reviewed": 1500,
    "unchanged": 1320,
    "upgraded": 98,
    "downgraded": 62,
    "constraint_violations_fixed": 20,
    "distribution_after": {
      "easy": 280,
      "medium": 520,
      "hard": 450,
      "expert": 250
    },
    "distribution_by_knowledge_type": {
      "Factual": {"easy": 280, "medium": 300, "hard": 120, "expert": 50},
      "Conceptual": {"easy": 0, "medium": 220, "hard": 180, "expert": 100},
      "Procedural": {"easy": 0, "medium": 0, "hard": 100, "expert": 50},
      "Metacognitive": {"easy": 0, "medium": 0, "hard": 50, "expert": 50}
    }
  }
}
```

---

## Constraints

- Do NOT assign "easy" to any Procedural or Metacognitive item.
- Do NOT assign "medium" to any Metacognitive item.
- Do NOT calibrate difficulty based on disease rarity alone. A question about a rare disease can be easy if it only requires recalling its name.
- Do NOT calibrate difficulty based on question length. A long question can be easy; a short question can be expert.
- Do NOT change the `knowledge_type` during difficulty calibration. If a knowledge_type mismatch is detected, flag it for upstream correction and calibrate difficulty based on the current knowledge_type.
- Do NOT approve a difficulty label without counting the reasoning steps. The step count must appear in the calibration output.
- When the item falls between two difficulty levels, assign the higher level. Over-estimation is less harmful than under-estimation for benchmark validity.
