"""Pydantic schemas for OralBench QA items, evaluation results, and flow state."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────

class KnowledgeType(str, Enum):
    FACTUAL = "Factual"
    CONCEPTUAL = "Conceptual"
    PROCEDURAL = "Procedural"
    METACOGNITIVE = "Metacognitive"


class Dimension(str, Enum):
    D1_ANATOMY_PHYSIOLOGY = "D1"
    D2_DISEASE_CHARACTERISTICS = "D2"
    D3_MATERIALS_PHARMACOLOGY = "D3"
    D4_PATHOLOGICAL_MECHANISM = "D4"
    D5_DIFFERENTIAL_DIAGNOSIS = "D5"
    D6_TREATMENT_RATIONALE = "D6"
    D7_CLINICAL_DECISION = "D7"
    D8_MULTIDISCIPLINARY_CASE = "D8"
    D9_COGNITIVE_MONITORING = "D9"
    D10_REASONING_REFLECTION = "D10"


class Subspecialty(str, Enum):
    ENDODONTICS = "Operative Dentistry & Endodontics"
    PERIODONTOLOGY = "Periodontology"
    ORAL_SURGERY = "Oral & Maxillofacial Surgery"
    PROSTHODONTICS = "Prosthodontics"
    ORTHODONTICS = "Orthodontics"
    PEDIATRIC = "Pediatric Dentistry"
    ORAL_MEDICINE = "Oral Medicine"
    IMPLANTOLOGY = "Implantology"
    PREVENTIVE = "Preventive Dentistry"
    BASIC_SCIENCES = "Basic Oral Sciences"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class SourceType(str, Enum):
    TEXTBOOK = "textbook"
    GUIDELINE = "guideline"
    EXAM = "exam"
    CASE_REPORT = "case_report"
    WEB = "web"


class QuestionFormat(str, Enum):
    MULTIPLE_CHOICE = "multiple-choice"
    OPEN_ENDED = "open-ended"
    METACOGNITIVE_OPEN = "metacognitive-open"
    METACOGNITIVE_ANALYSIS = "metacognitive-analysis"


class ReviewStatus(str, Enum):
    AUTO_APPROVED = "auto_approved"
    AUTO_REVISED = "auto_revised"
    HUMAN_REVIEWED = "human_reviewed"
    REJECTED = "rejected"


class EfficiencyCategory(str, Enum):
    CITATION = "Citation"
    REPETITION = "Repetition"
    REASONING = "Reasoning"
    REDUNDANCY = "Redundancy"


# ── Source Reference ───────────────────────────────────────────────────────

class SourceReference(BaseModel):
    title: str = ""
    authors: str = ""
    year: Optional[int] = None
    doi_or_url: str = ""
    page_or_section: str = ""


# ── Evaluation Criteria (embedded in QA item) ─────────────────────────────

class EvaluationCriteria(BaseModel):
    factuality: str = ""
    completeness: str = ""
    key_points: list[str] = Field(default_factory=list)


# ── QA Item ────────────────────────────────────────────────────────────────

class QAItem(BaseModel):
    """Core schema for a single OralBench QA item."""

    question_id: str
    knowledge_type: KnowledgeType
    dimension: Dimension
    subspecialty: list[Subspecialty]
    difficulty: Difficulty
    source_type: SourceType
    source_reference: SourceReference = Field(default_factory=SourceReference)
    question_format: QuestionFormat
    question: str
    options: list[str] = Field(default_factory=list)
    answer: str = ""
    reference_answer: str = ""
    explanation: str = ""
    evaluation_criteria: EvaluationCriteria = Field(default_factory=EvaluationCriteria)
    language: str = "en"
    generation_model: str = ""
    review_status: ReviewStatus = ReviewStatus.AUTO_APPROVED
    reviewer_notes: str = ""


# ── Step-Level Evaluation ──────────────────────────────────────────────────

class JudgmentPathEntry(BaseModel):
    judgment: str = ""
    question_to_search: str = ""
    info: str = ""


class StepEvaluation(BaseModel):
    """Evaluation result for a single reasoning step."""

    step: str
    efficiency: EfficiencyCategory
    factuality: Optional[bool] = None
    judgment_path: list[JudgmentPathEntry] = Field(default_factory=list)


class GTStepEvaluation(BaseModel):
    """Whether a ground-truth step was covered by the model output."""

    step: str
    hit: bool


# ── Per-Item Scoring Result ────────────────────────────────────────────────

class ClassicalScores(BaseModel):
    is_correct: Optional[bool] = None


class NLUScores(BaseModel):
    bert_score: Optional[float] = None
    rouge_l: Optional[float] = None
    bleu: Optional[float] = None
    semantic_similarity: Optional[float] = None


class StepLevelScores(BaseModel):
    evaluated_steps: list[StepEvaluation] = Field(default_factory=list)
    efficiency_score: Optional[float] = None
    factuality_score: Optional[float] = None


class CompletenessScores(BaseModel):
    gt_steps: list[GTStepEvaluation] = Field(default_factory=list)
    recall_score: Optional[float] = None


class HolisticScores(BaseModel):
    clarity: Optional[int] = None       # 1-5


class CalibrationScores(BaseModel):
    stated_confidence: Optional[float] = None
    boundary_recognized: Optional[bool] = None
    self_corrected: Optional[bool] = None


class ItemEvaluation(BaseModel):
    """Complete evaluation result for one QA item + one model."""

    question_id: str
    model_name: str
    model_response: str = ""
    classical: ClassicalScores = Field(default_factory=ClassicalScores)
    nlu: NLUScores = Field(default_factory=NLUScores)
    step_level: StepLevelScores = Field(default_factory=StepLevelScores)
    completeness: CompletenessScores = Field(default_factory=CompletenessScores)
    holistic: HolisticScores = Field(default_factory=HolisticScores)
    calibration: CalibrationScores = Field(default_factory=CalibrationScores)


# ── Aggregated Model Scores ────────────────────────────────────────────────

class AggregatedScores(BaseModel):
    """Aggregated scores for one model across the benchmark."""

    model_name: str
    total_items: int = 0
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    avg_bert_score: Optional[float] = None
    avg_rouge_l: Optional[float] = None
    avg_efficiency: Optional[float] = None
    avg_factuality: Optional[float] = None
    avg_completeness_recall: Optional[float] = None
    avg_clarity: Optional[float] = None
    ece: Optional[float] = None
    mce: Optional[float] = None
    boundary_recognition_rate: Optional[float] = None
    self_correction_rate: Optional[float] = None
    # Per-dimension breakdown
    scores_by_dimension: dict[str, dict[str, float]] = Field(default_factory=dict)
    scores_by_subspecialty: dict[str, dict[str, float]] = Field(default_factory=dict)
    scores_by_difficulty: dict[str, dict[str, float]] = Field(default_factory=dict)


# ── Flow State ─────────────────────────────────────────────────────────────

class OralBenchState(BaseModel):
    """State passed between phases in the CrewAI Flow."""

    # Phase 1 outputs
    extracted_content: list[dict] = Field(default_factory=list)
    case_reports: list[dict] = Field(default_factory=list)

    # Phase 2 outputs
    generated_items: list[QAItem] = Field(default_factory=list)
    reviewed_items: list[QAItem] = Field(default_factory=list)

    # Phase 3 outputs
    model_responses: dict[str, list[dict]] = Field(default_factory=dict)  # model_name -> responses
    evaluations: list[ItemEvaluation] = Field(default_factory=list)
    aggregated: list[AggregatedScores] = Field(default_factory=list)
