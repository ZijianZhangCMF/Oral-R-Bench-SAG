---
name: case-report-extraction
description: Extract structured clinical data from oral medicine case report full text into standardized JSON fields. Use when processing PMC case reports for QA generation or clinical scenario construction.
metadata:
  author: OralBench Team
  version: "1.0.0"
---

# Case Report Extraction

## Input

Accept full-text case reports from PubMed Central (PMC) Open Access, provided as plain text or HTML. Each input must include the `pmcid` for traceability.

## Output Schema

Produce one JSON object per case report:

```json
{
  "pmcid": "PMC9876543",
  "doi": "10.1234/example.2023.001",
  "title": "Oral Verrucous Carcinoma Mimicking Leukoplakia: A Case Report",
  "chief_complaint": "Non-healing white patch on the left buccal mucosa for 6 months",
  "history_present_illness": "A 62-year-old male presented with...",
  "physical_examination": "Extraoral: no cervical lymphadenopathy. Intraoral: 3x2 cm verrucous white plaque on left buccal mucosa...",
  "auxiliary_examination": "Incisional biopsy revealed well-differentiated squamous epithelium with...",
  "diagnosis": "Oral verrucous carcinoma",
  "differential_diagnosis": "Verrucous leukoplakia, squamous cell carcinoma, verrucous hyperplasia",
  "treatment": "Wide surgical excision with 1 cm margins. No neck dissection performed.",
  "outcome": "Complete excision confirmed on histopathology. No recurrence at 6-month follow-up.",
  "follow_up": "Patient followed every 3 months with clinical examination for 2 years."
}
```

## Extraction Procedure

### 1. Identify Case Report Sections

Map the source text to the output fields using these section-heading patterns:

| Output Field | Common Section Headings |
|-------------|------------------------|
| `chief_complaint` | "Chief complaint", "Presenting complaint", "Reason for visit" |
| `history_present_illness` | "History of present illness", "Case presentation", "Case report", "Clinical history" |
| `physical_examination` | "Physical examination", "Clinical examination", "Clinical findings", "Examination" |
| `auxiliary_examination` | "Investigations", "Laboratory findings", "Imaging", "Histopathology", "Radiographic findings" |
| `diagnosis` | "Diagnosis", "Final diagnosis" |
| `differential_diagnosis` | "Differential diagnosis", "Differential diagnoses" |
| `treatment` | "Treatment", "Management", "Therapeutic intervention", "Surgical procedure" |
| `outcome` | "Outcome", "Results", "Postoperative course" |
| `follow_up` | "Follow-up", "Follow up", "Prognosis" |

When a case report does not use standard section headings, extract information by semantic content matching within the narrative.

### 2. Extract Each Field

For each output field:
1. Locate the relevant text span in the source.
2. Extract the substantive clinical content. Remove filler phrases like "We present a case of..." or "Written informed consent was obtained."
3. Preserve all clinical details: measurements, lab values, drug names, dosages, durations.
4. If multiple examinations or treatments occurred over time, present them in chronological order.

### 3. Handle Auxiliary Examinations

The `auxiliary_examination` field aggregates all non-physical diagnostic information. Combine these subsections if present:
- Laboratory results (blood work, cultures, serology)
- Imaging findings (radiographs, CT, MRI, ultrasound)
- Histopathological findings (biopsy results)
- Special tests (immunohistochemistry, molecular studies)

Prefix each subsection within the field: `"Lab: ...", "Imaging: ...", "Histopathology: ..."`.

### 4. Handle Missing Fields

If a field is not present in the source text, set its value to `""` (empty string).

Do NOT fabricate content to fill missing fields. Do NOT infer clinical details not explicitly stated.

### 5. Handle Multi-Patient Reports

If a single paper describes multiple cases, produce one JSON object per case. Add a `case_number` field (1-indexed) to each.

## Validation Rules

1. `pmcid` must be non-empty and match the pattern `PMC\d+`.
2. `diagnosis` must be non-empty — if no diagnosis is stated, set to `"Not specified"` and add `"extraction_warning": "no_diagnosis_found"`.
3. `chief_complaint` and `history_present_illness` should not be identical. If they overlap significantly, keep the shorter version in `chief_complaint` and the full narrative in `history_present_illness`.
4. No field should contain reference citations (e.g., "[1]", "(Smith et al., 2020)"). Strip these during extraction.
5. No field should contain figure/table references (e.g., "as shown in Figure 2"). Remove the reference but keep the described finding.

## Constraints

- Do NOT fabricate any clinical information not present in the source text.
- Do NOT interpret or add clinical reasoning not stated in the paper.
- Do NOT include author commentary, literature review content, or discussion-section opinions as clinical data.
- Do NOT include consent statements, ethics declarations, or conflict-of-interest disclosures.
- Do NOT include figure or table data that cannot be represented as text — note their existence in an `"excluded_figures"` array if relevant clinical data is locked in images.
- Use empty string `""` for any field not found in the source. Do NOT use `null`, `"N/A"`, or `"Not mentioned"`.
