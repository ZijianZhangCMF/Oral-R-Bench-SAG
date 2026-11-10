"""QA Generation Crew — 1 agent: QA Generator with 5 skills.

Strategy: one source document per task. Strict dimension assignment rules.
Data source → knowledge level mapping:
  - Exam questions (as inspiration) → L1, L2, L3
  - PDF (textbooks + guidelines) → L1, L2, L3, L4
  - Case Reports → L3, L4
"""

from crewai import Agent, Crew, Process, Task

SKILLS_DIR = "./src/dentalbench/skills"

DIMENSION_RULES = """\
STRICT dimension assignment — follow exactly:

D1 (Anatomy & Physiology): ONLY anatomy, histology, embryology, physiology, innervation, blood supply, tooth morphology.
D2 (Disease Characteristics): ONLY disease classification, clinical features, diagnostic criteria, epidemiology, pathognomonic signs. NOT treatment, NOT materials, NOT drugs.
D3 (Materials & Pharmacology): ONLY dental materials, drugs, cements, alloys, composites, pharmacology, drug interactions. If the question is about a MATERIAL or DRUG, it is D3 regardless of clinical context.

D4 (Pathological Mechanism): ONLY "why/how does this disease happen" — pathogenesis, etiology, molecular mechanisms.
D5 (Differential Diagnosis): ONLY "how to distinguish between conditions" — comparing features of 2+ diseases.
D6 (Treatment Rationale): ONLY "why choose this treatment" — justification of treatment decisions.

D7 (Clinical Decision & Planning): Clinical scenarios requiring diagnosis + treatment plan + recommended tests.
D8 (Multidisciplinary Case): Complex cases requiring coordination across specialties (MDT).

D9 (Cognitive Monitoring & Uncertainty): Confidence calibration, knowledge boundaries, information gaps.
D10 (Reasoning Reflection & Critical Thinking): Analyzing reasoning chains, identifying biases, evidence appraisal.

COMMON MISTAKES TO AVOID:
- A question about a DRUG or MATERIAL property is D3, NOT D2
- A question about "what are the features of disease X" is D2, NOT D4 (D4 requires explaining WHY/HOW)
- Do NOT reference the source document in the question (no "According to the textbook...", no "Based on the guideline...")
- Every question must be answerable by a clinician WITHOUT access to the source document
- Do NOT ask about "advances" or "overview" of a field — ask about specific clinical knowledge

OPEN-ENDED QUESTION STEM RULES:
- Keep question stems CONCISE (1-2 sentences after the scenario).
- Do NOT pre-list answer points in the question. No "Include the roles of X, Y, Z...", no "Discuss the following aspects...", no "Address A, B, and C...".
- BAD: "Explain the mechanism by which X causes Y. Include the roles of A, B, C, and D."
- GOOD: "A patient reports pain after placement of a metallic restoration opposing a gold crown. Explain the likely mechanism."
- The detailed answer points belong in reference_answer, NOT in the question stem."""

QA_SCHEMA = """\
Output ONLY a JSON array (no markdown fences, no extra text). Each item MUST have ALL these fields:
{
  "question_id": "OB_<D1-D10>_<ABBREV>_<NNN>",
  "knowledge_type": "Factual|Conceptual|Procedural|Metacognitive",
  "dimension": "D1|D2|D3|D4|D5|D6|D7|D8|D9|D10",
  "subspecialty": ["one or more from: Operative Dentistry & Endodontics, Periodontology, Oral & Maxillofacial Surgery, Prosthodontics, Orthodontics, Pediatric Dentistry, Oral Medicine, Implantology, Preventive Dentistry, Basic Oral Sciences"],
  "difficulty": "easy|medium|hard|expert",
  "source_type": "textbook|guideline|exam|case_report",
  "source_reference": {"title": "source document title", "authors": "", "year": null, "doi_or_url": "", "page_or_section": ""},
  "question_format": "multiple-choice|open-ended|metacognitive-open|metacognitive-analysis",
  "question": "the question text",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "answer": "A|B|C|D (for MC) or empty string (for open-ended)",
  "reference_answer": "detailed reference answer (>50 chars for open-ended)",
  "explanation": "why this answer is correct"
}
For open-ended items: set options to [] and answer to "".
ALL content must be in English."""


def qa_generator() -> Agent:
    return Agent(
        role="QA Generator",
        goal=(
            "Generate high-quality original oral medicine QA items in English. "
            "Each item must target a specific knowledge level and dimension with strict accuracy. "
            "Use source material as inspiration only — never copy verbatim or reference the source."
        ),
        backstory=(
            "You are a senior dental education specialist who designs exam questions "
            "for licensing boards. You are meticulous about dimension classification "
            "and never confuse materials/drugs (D3) with disease features (D2)."
        ),
        skills=[
            f"{SKILLS_DIR}/qa-factual",
            f"{SKILLS_DIR}/qa-conceptual",
            f"{SKILLS_DIR}/qa-procedural",
            f"{SKILLS_DIR}/qa-metacognitive",
            f"{SKILLS_DIR}/oral-medicine-taxonomy",
        ],
        llm="gpt-5",
        max_tokens=8192,
        verbose=True,
    )


def generate_factual_task(agent: Agent, source_text: str = "", source_title: str = "") -> Task:
    return Task(
        description=(
            f"Generate L1 Factual QA items from the following SINGLE source document.\n\n"
            f"Source: {source_title}\n"
            f"Allowed dimensions: D1, D2, D3 ONLY.\n"
            f"Format: multiple-choice (4 options A-D) and short open-ended.\n\n"
            f"{DIMENSION_RULES}\n\n"
            f"Source material (use as INSPIRATION only):\n---\n{source_text[:5000]}\n---\n\n"
            f"{QA_SCHEMA}"
        ),
        expected_output="JSON array of QAItem objects with ALL fields populated.",
        agent=agent,
    )


def generate_conceptual_task(agent: Agent, source_text: str = "", source_title: str = "") -> Task:
    return Task(
        description=(
            f"Generate L2 Conceptual QA items from the following SINGLE source document.\n\n"
            f"Source: {source_title}\n"
            f"Allowed dimensions: D4, D5, D6 ONLY.\n"
            f"Format: open-ended. Focus on 'why' and 'how' questions requiring reasoning.\n"
            f"D4 = explain pathogenesis/mechanism. D5 = compare/distinguish conditions. D6 = justify treatment choice.\n\n"
            f"{DIMENSION_RULES}\n\n"
            f"Source material (use as INSPIRATION only):\n---\n{source_text[:5000]}\n---\n\n"
            f"{QA_SCHEMA}"
        ),
        expected_output="JSON array of QAItem objects with ALL fields populated.",
        agent=agent,
    )


def generate_procedural_task(agent: Agent, source_text: str = "", source_title: str = "") -> Task:
    return Task(
        description=(
            f"Generate L3 Procedural QA items from the following SINGLE source document.\n\n"
            f"Source: {source_title}\n"
            f"Allowed dimensions: D7, D8 ONLY.\n"
            f"Format: open-ended. Present clinical scenarios requiring multi-step reasoning.\n"
            f"D7 = diagnosis + treatment plan + tests. D8 = MDT coordination across specialties.\n\n"
            f"{DIMENSION_RULES}\n\n"
            f"Source material (use as INSPIRATION only):\n---\n{source_text[:5000]}\n---\n\n"
            f"{QA_SCHEMA}"
        ),
        expected_output="JSON array of QAItem objects with ALL fields populated.",
        agent=agent,
    )


def generate_metacognitive_task(agent: Agent, source_text: str = "", source_title: str = "") -> Task:
    return Task(
        description=(
            f"Generate L4 Metacognitive QA items from the following SINGLE source document.\n\n"
            f"Source: {source_title}\n"
            f"Allowed dimensions: D9, D10 ONLY. Do NOT use exam questions as source for this level.\n"
            f"Format: metacognitive-open and metacognitive-analysis (mix both).\n"
            f"D9 = confidence calibration, uncertainty, knowledge boundaries.\n"
            f"D10 = analyze reasoning chains, identify biases, appraise evidence.\n\n"
            f"{DIMENSION_RULES}\n\n"
            f"Source material (use as INSPIRATION only):\n---\n{source_text[:5000]}\n---\n\n"
            f"{QA_SCHEMA}"
        ),
        expected_output="JSON array of QAItem objects with ALL fields populated.",
        agent=agent,
    )


def create_generation_crew(
    knowledge_type: str = "Factual",
    source_text: str = "",
    source_title: str = "",
) -> Crew:
    """Create a crew for generating QA items of a specific knowledge type from a single source."""
    generator = qa_generator()

    task_map = {
        "Factual": generate_factual_task,
        "Conceptual": generate_conceptual_task,
        "Procedural": generate_procedural_task,
        "Metacognitive": generate_metacognitive_task,
    }

    task_fn = task_map.get(knowledge_type, generate_factual_task)
    task = task_fn(generator, source_text=source_text, source_title=source_title)

    return Crew(
        agents=[generator],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
