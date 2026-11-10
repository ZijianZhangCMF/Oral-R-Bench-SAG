"""QA Review Crew — 1 agent: QA Reviewer with 4 skills.

Checks dimension accuracy, question quality, originality, and format compliance.
"""

from crewai import Agent, Crew, Process, Task
from crewai_tools import FileReadTool

from dentalbench.tools.embedding_similarity_tool import EmbeddingSimilarityTool

SKILLS_DIR = "./src/dentalbench/skills"

DIMENSION_RULES = """\
STRICT dimension assignment — verify each item against these rules:

D1 (Anatomy & Physiology): ONLY anatomy, histology, embryology, physiology, innervation, blood supply, tooth morphology.
D2 (Disease Characteristics): ONLY disease classification, clinical features, diagnostic criteria, epidemiology. NOT treatment, NOT materials, NOT drugs.
D3 (Materials & Pharmacology): ONLY dental materials, drugs, cements, alloys, composites, pharmacology. If about a MATERIAL or DRUG → D3 regardless of context.

D4 (Pathological Mechanism): ONLY "why/how does this disease happen" — pathogenesis, etiology.
D5 (Differential Diagnosis): ONLY "how to distinguish between conditions" — comparing 2+ diseases.
D6 (Treatment Rationale): ONLY "why choose this treatment" — justification.

D7 (Clinical Decision & Planning): Clinical scenarios requiring diagnosis + treatment plan + tests.
D8 (Multidisciplinary Case): Complex cases requiring MDT coordination.

D9 (Cognitive Monitoring & Uncertainty): Confidence calibration, knowledge boundaries.
D10 (Reasoning Reflection & Critical Thinking): Analyzing reasoning chains, identifying biases.

REJECT if:
- Drug/material question labeled D2 (should be D3)
- "What are features of X" labeled D4 (should be D2; D4 requires WHY/HOW)
- Question references source document ("According to...", "Based on the textbook...")
- Question asks about "advances" or "overview" of a field
- Question is answerable only with access to the source document
- Open-ended question stem pre-lists answer points ("Include the roles of X, Y, Z...", "Discuss the following aspects...", "Address A, B, and C...")
- Open-ended question stem is longer than 3 sentences (scenario excluded) — the question portion after the scenario should be 1 sentence"""


def qa_reviewer() -> Agent:
    return Agent(
        role="QA Reviewer",
        goal=(
            "Review QA items for dimension accuracy, question quality, and originality. "
            "Fix misclassified dimensions. Reject low-quality or source-referencing items."
        ),
        backstory=(
            "You are a senior dental examiner and quality assurance specialist. "
            "You are especially strict about dimension classification — a drug question "
            "is always D3, never D2. You reject any question that references its source."
        ),
        skills=[
            f"{SKILLS_DIR}/factuality-review",
            f"{SKILLS_DIR}/deduplication",
            f"{SKILLS_DIR}/difficulty-calibration",
            f"{SKILLS_DIR}/format-validation",
        ],
        tools=[FileReadTool(), EmbeddingSimilarityTool()],
        llm="gpt-5",
        max_tokens=8192,
        verbose=True,
    )


def review_task(agent: Agent, items_json: str = "") -> Task:
    return Task(
        description=(
            f"Review these QA items through 5 checks:\n\n"
            f"1. DIMENSION CHECK (most important): Verify each item's dimension using these rules:\n"
            f"{DIMENSION_RULES}\n\n"
            f"2. QUALITY CHECK: Reject items that:\n"
            f"   - Reference the source document ('According to...', 'Based on the guideline...')\n"
            f"   - Ask about 'advances', 'overview', or 'recent developments' in a field\n"
            f"   - Are too vague, trivial, or have ambiguous answers\n"
            f"   - Have incorrect MC answers\n\n"
            f"3. ORIGINALITY CHECK: For exam-sourced items, verify they are genuinely "
            f"regenerated, not verbatim translations of Chinese exam questions.\n\n"
            f"4. DIFFICULTY CHECK: Validate difficulty labels match the rubric.\n\n"
            f"5. FORMAT CHECK: Required fields present, MC answer in options, "
            f"reference_answer >50 chars for open-ended.\n\n"
            f"For each item: APPROVE (keep), FIX (correct dimension/difficulty + add reviewer_notes), "
            f"or REJECT (remove). Output ONLY the approved+fixed items as a JSON array.\n\n"
            f"Items to review:\n{items_json}"
        ),
        expected_output="JSON array of approved/fixed QA items (rejected items excluded).",
        agent=agent,
    )


def create_review_crew(items_json: str = "") -> Crew:
    """Create a review crew that checks a batch of QA items."""
    reviewer = qa_reviewer()

    return Crew(
        agents=[reviewer],
        tasks=[review_task(reviewer, items_json=items_json)],
        process=Process.sequential,
        verbose=True,
    )
