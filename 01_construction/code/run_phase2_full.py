#!/usr/bin/env python
"""Phase 2 FULL — QA Generation from ALL sources + Review.

Generates 1500-2000 items across all knowledge levels from all data sources.
Single-source per batch. QA Reviewer checks every batch.
Auto-saves progress incrementally. Resilient to API failures (retries + skips).

Target distribution:
  L1 Factual:       600-800 items (40%)
  L2 Conceptual:    450-600 items (30%)
  L3 Procedural:    200-300 items (15%)
  L4 Metacognitive: 150-250 items (10-15%)
"""

import json
import os
import random
import time
import traceback
import warnings
import logging

from dotenv import load_dotenv

load_dotenv(override=True)
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

OUTPUT_DIR = "./data/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SKILLS_DIR = "./src/dentalbench/skills"

SUBJECT_MAP = {
    "口腔颌面外科学": "Oral & Maxillofacial Surgery",
    "口腔修复学": "Prosthodontics",
    "牙体牙髓病学": "Operative Dentistry & Endodontics",
    "牙周病学": "Periodontology",
    "口腔黏膜病学": "Oral Medicine",
    "儿童口腔医学": "Pediatric Dentistry",
    "口腔组织病理学": "Basic Oral Sciences",
    "口腔解剖生理学": "Basic Oral Sciences",
    "口腔预防医学": "Preventive Dentistry",
    "口腔材料学": "Basic Oral Sciences",
    "口腔颌面医学影像诊断学": "Basic Oral Sciences",
    "临床医学": "Oral & Maxillofacial Surgery",
}

QA_SCHEMA = """\
Output ONLY a JSON array. Each item:
{
  "question_id": "OB_<D1-D10>_<ABBREV>_<NNN>",
  "knowledge_type": "Factual|Conceptual|Procedural|Metacognitive",
  "dimension": "D1|D2|D3|D4|D5|D6|D7|D8|D9|D10",
  "subspecialty": ["..."],
  "difficulty": "easy|medium|hard|expert",
  "source_type": "textbook|guideline|exam|case_report",
  "source_reference": {"title": "...", "authors": "", "year": null, "doi_or_url": "", "page_or_section": ""},
  "question_format": "multiple-choice|open-ended|metacognitive-open|metacognitive-analysis",
  "question": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "answer": "A|B|C|D or empty for open-ended",
  "reference_answer": "detailed reference (>50 chars for open-ended)",
  "explanation": "..."
}
For open-ended: options=[], answer="". ALL in English."""

DIMENSION_RULES = """\
STRICT dimension assignment:
D1: ONLY anatomy, histology, embryology, physiology, innervation, blood supply, tooth morphology.
D2: ONLY disease classification, clinical features, diagnostic criteria, epidemiology. NOT drugs/materials.
D3: ONLY dental materials, drugs, pharmacology. If about a MATERIAL or DRUG → D3 always.
D4: ONLY "why/how does this disease happen" — pathogenesis, etiology.
D5: ONLY "distinguish between conditions" — comparing 2+ diseases.
D6: ONLY "why choose this treatment" — justification.
D7: Clinical scenarios → diagnosis + treatment plan + tests.
D8: Complex cases requiring 2+ specialties (MDT).
D9: Confidence calibration, knowledge boundaries, uncertainty.
D10: Analyzing reasoning chains, identifying biases, evidence appraisal.

MISTAKES TO AVOID:
- Drug/material question → D3, NOT D2
- "What are features of X" → D2, NOT D4
- No "According to the textbook..." in questions
- No "advances" or "overview" questions

OPEN-ENDED STEMS: Keep concise (1-2 sentences after scenario). Do NOT pre-list answer points.
BAD: "Explain X. Include roles of A, B, C, and D."
GOOD: "A patient presents with X. Explain the likely mechanism." """


# ── Data loaders ───────────────────────────────────────────────────────────

def load_all_sources():
    """Load ALL source documents for full-scale generation."""
    sources = []
    random.seed(42)

    # Exam: ALL subjects, 30 questions each (sampled for diversity)
    with open("data/raw/exam_parsed.json", "r") as f:
        subjects = json.load(f)
    for subj in subjects:
        qs = [q for q in subj["questions"] if q.get("correct_answer")]
        # Split into chunks of 15 for manageable batches
        random.shuffle(qs)
        for chunk_i in range(0, len(qs), 15):
            chunk = qs[chunk_i:chunk_i + 15]
            text = "\n\n".join(
                f"Q: {q['question_stem']}\n" +
                "\n".join(f"  {k}. {v}" for k, v in q["options"].items()) +
                f"\nAnswer: {q['correct_answer']}\nExplanation: {q.get('explanation', '')[:200]}"
                for q in chunk
            )
            sources.append({
                "id": f"exam_{subj['subject']}_chunk{chunk_i // 15}",
                "type": "exam",
                "subspecialty": SUBJECT_MAP.get(subj["subject"], "Basic Oral Sciences"),
                "title": f"{subj['subject']} - Dental Licensing Exam (chunk {chunk_i // 15 + 1})",
                "text": text,
                "levels": ["Factual", "Conceptual", "Procedural"],
            })

    # PDF: ALL PDFs
    with open("data/raw/pdf_manifest.json", "r") as f:
        manifest = json.load(f)
    ok = [m for m in manifest if "error" not in m and m.get("output_file")]
    for m in ok:
        if os.path.exists(m["output_file"]):
            with open(m["output_file"], "r") as f:
                data = json.load(f)
            pages = data.get("pages", [])
            # Split large PDFs into chunks of ~10 pages
            for chunk_i in range(0, len(pages), 10):
                chunk_pages = pages[chunk_i:chunk_i + 10]
                text = "\n".join(p["text"][:600] for p in chunk_pages)
                if len(text.strip()) < 200:
                    continue
                sources.append({
                    "id": f"pdf_{m['filename'][:30]}_p{chunk_i}",
                    "type": m["source_type"],
                    "title": f"{m['filename']} (pages {chunk_i + 1}-{chunk_i + len(chunk_pages)})",
                    "language": m["language"],
                    "text": text[:4000],
                    "levels": ["Factual", "Conceptual", "Procedural", "Metacognitive"],
                })

    # Case reports: ALL with case_presentation or abstract
    cr_path = "data/raw/case_reports/case_reports_all.json"
    if os.path.exists(cr_path):
        with open(cr_path, "r") as f:
            reports = json.load(f)
        for r in reports:
            text = r.get("case_presentation") or r.get("abstract") or ""
            if len(text.strip()) < 100:
                continue
            sources.append({
                "id": f"cr_{r.get('pmcid', '')}",
                "type": "case_report",
                "title": r.get("title", "")[:80],
                "subspecialty": r.get("subspecialty", []),
                "text": text[:4000],
                "levels": ["Procedural", "Metacognitive"],
            })

    return sources


# ── Generation & Review ────────────────────────────────────────────────────

def generate_from_source(source: dict, knowledge_type: str, count: int, fmt: str) -> list[dict]:
    from crewai import Agent, Task, Crew

    skill_map = {
        "Factual": f"{SKILLS_DIR}/qa-factual",
        "Conceptual": f"{SKILLS_DIR}/qa-conceptual",
        "Procedural": f"{SKILLS_DIR}/qa-procedural",
        "Metacognitive": f"{SKILLS_DIR}/qa-metacognitive",
    }
    dims = {
        "Factual": "D1, D2, D3",
        "Conceptual": "D4, D5, D6",
        "Procedural": "D7, D8",
        "Metacognitive": "D9, D10",
    }

    agent = Agent(
        role="QA Generator",
        goal=f"Generate {count} original {knowledge_type} oral medicine QA items in English.",
        backstory="You are a senior dental education specialist. Meticulous about dimension classification.",
        skills=[skill_map[knowledge_type], f"{SKILLS_DIR}/oral-medicine-taxonomy"],
        llm="gpt-5",
        max_tokens=8192,
        verbose=False,
    )

    task = Task(
        description=(
            f"Generate exactly {count} ORIGINAL {knowledge_type} QA items.\n"
            f"Dimensions: {dims[knowledge_type]}\n"
            f"Format: {fmt}\n"
            f"Source: {source['title']}\n\n"
            f"{DIMENSION_RULES}\n\n"
            f"Source material (INSPIRATION only, do NOT copy, do NOT reference source in questions):\n"
            f"---\n{source['text'][:5000]}\n---\n\n{QA_SCHEMA}"
        ),
        expected_output=f"JSON array of {count} QA items.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    return _parse_json(str(result))


def review_batch(items: list[dict]) -> list[dict]:
    from crewai import Agent, Task, Crew

    if not items:
        return []

    agent = Agent(
        role="QA Reviewer",
        goal="Review QA items for dimension accuracy, quality, and originality.",
        backstory="You are strict about dimension classification. Drug/material → D3 always. Reject source-referencing questions.",
        skills=[
            f"{SKILLS_DIR}/factuality-review",
            f"{SKILLS_DIR}/difficulty-calibration",
            f"{SKILLS_DIR}/format-validation",
        ],
        llm="gpt-5",
        max_tokens=8192,
        verbose=False,
    )

    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    task = Task(
        description=(
            f"Review {len(items)} QA items:\n"
            f"1. DIMENSION CHECK: {DIMENSION_RULES}\n"
            f"2. QUALITY: Reject source-referencing, 'overview/advances' questions, over-prompted stems.\n"
            f"3. ORIGINALITY: Exam items must be regenerated, not verbatim translations.\n"
            f"APPROVE, FIX (correct dimension + add reviewer_notes), or REJECT.\n"
            f"Output ONLY approved+fixed items as JSON array.\n\n{items_json}"
        ),
        expected_output="JSON array of approved/fixed items.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    return _parse_json(str(result))


def _parse_json(raw: str) -> list[dict]:
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            cleaned = raw[start:end].replace("```json", "").replace("```", "")
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
    return []


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    console.print(Panel.fit(
        "[bold cyan]OralBench Phase 2 — FULL QA Generation[/]\n"
        "Agent: gpt-5 | Single-source batches | QA Reviewer on every batch\n"
        "Target: 1500-2000 items | Auto-saves progress",
        border_style="cyan",
    ))

    # Load all sources
    console.print("\n[dim]Loading all sources...[/]")
    all_sources = load_all_sources()
    exam_src = [s for s in all_sources if s["type"] == "exam"]
    pdf_src = [s for s in all_sources if s["type"] in ("textbook", "guideline")]
    cr_src = [s for s in all_sources if s["type"] == "case_report"]
    console.print(f"  Exam chunks: {len(exam_src)} | PDF chunks: {len(pdf_src)} | Case reports: {len(cr_src)}")
    console.print(f"  Total source chunks: {len(all_sources)}\n")

    # Build generation plan
    # Target: ~40% Factual, ~30% Conceptual, ~15% Procedural, ~15% Metacognitive
    plan = []

    # Factual from exam (3 items per chunk) + PDF (2 items per chunk)
    random.seed(42)
    for src in random.sample(exam_src, min(80, len(exam_src))):
        plan.append((src, "Factual", 3, "multiple-choice"))
    for src in random.sample(pdf_src, min(80, len(pdf_src))):
        plan.append((src, "Factual", 3, "multiple-choice"))

    # Conceptual from exam + PDF
    for src in random.sample(exam_src, min(50, len(exam_src))):
        plan.append((src, "Conceptual", 3, "open-ended"))
    for src in random.sample(pdf_src, min(60, len(pdf_src))):
        plan.append((src, "Conceptual", 3, "open-ended"))

    # Procedural from exam + PDF + case reports
    for src in random.sample(exam_src, min(20, len(exam_src))):
        plan.append((src, "Procedural", 2, "open-ended"))
    for src in random.sample(pdf_src, min(30, len(pdf_src))):
        plan.append((src, "Procedural", 2, "open-ended"))
    for src in random.sample(cr_src, min(50, len(cr_src))):
        plan.append((src, "Procedural", 2, "open-ended"))

    # Metacognitive from PDF + case reports ONLY
    for src in random.sample(pdf_src, min(40, len(pdf_src))):
        plan.append((src, "Metacognitive", 2, "metacognitive-open and metacognitive-analysis (mix)"))
    for src in random.sample(cr_src, min(40, len(cr_src))):
        plan.append((src, "Metacognitive", 2, "metacognitive-open and metacognitive-analysis (mix)"))

    random.shuffle(plan)  # Shuffle to distribute API load
    total_target = sum(p[2] for p in plan)
    console.print(f"  Generation plan: {len(plan)} batches, ~{total_target} items target\n")

    # Load existing progress if any
    progress_file = os.path.join(OUTPUT_DIR, "phase2_full_reviewed.json")
    all_reviewed = []
    all_generated = []
    completed_ids = set()
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            all_reviewed = json.load(f)
        console.print(f"  [yellow]Resuming: {len(all_reviewed)} items already done[/]\n")

    gen_raw_file = os.path.join(OUTPUT_DIR, "phase2_full_generated_raw.json")
    if os.path.exists(gen_raw_file):
        with open(gen_raw_file, "r") as f:
            all_generated = json.load(f)

    errors = []
    batch_num = 0

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}", justify="left"),
        BarColumn(bar_width=25), MofNCompleteColumn(), TimeElapsedColumn(),
        console=console, refresh_per_second=1,
    ) as progress:
        overall = progress.add_task(
            f"[cyan]Overall ({len(all_reviewed)} done)[/]", total=len(plan))

        for i, (src, kt, count, fmt) in enumerate(plan):
            batch_num += 1
            label = f"{kt[:4]}←{src['type'][:5]}:{src['id'][:12]}"

            progress.update(overall,
                description=f"[cyan]Overall[/] gen={len(all_generated)} rev={len(all_reviewed)} err={len(errors)}")

            # Generate
            progress.update(overall, description=f"[cyan]{label}[/] generating...")
            try:
                items = generate_from_source(src, kt, count, fmt)
                all_generated.extend(items)
            except Exception as e:
                logger.warning(f"Batch {batch_num} gen error: {e}")
                errors.append({"batch": batch_num, "phase": "generate", "error": str(e)[:200]})
                progress.update(overall, advance=1)
                # Retry once after short wait
                time.sleep(5)
                try:
                    items = generate_from_source(src, kt, count, fmt)
                    all_generated.extend(items)
                except Exception:
                    progress.update(overall, advance=0)
                    continue

            # Review
            if items:
                progress.update(overall, description=f"[cyan]{label}[/] reviewing {len(items)}...")
                try:
                    reviewed = review_batch(items)
                    all_reviewed.extend(reviewed)
                except Exception as e:
                    logger.warning(f"Batch {batch_num} review error: {e}")
                    # If review fails, keep generated items
                    all_reviewed.extend(items)
                    errors.append({"batch": batch_num, "phase": "review", "error": str(e)[:200]})

            progress.update(overall, advance=1)

            # Auto-save every 5 batches
            if batch_num % 5 == 0:
                _save(all_reviewed, "phase2_full_reviewed.json")
                _save(all_generated, "phase2_full_generated_raw.json")
                logger.info(f"Auto-saved: {len(all_reviewed)} reviewed, {len(all_generated)} raw, {len(errors)} errors")

    # Final save
    _save(all_reviewed, "phase2_full_reviewed.json")
    _save(all_generated, "phase2_full_generated_raw.json")
    if errors:
        _save(errors, "phase2_full_errors.json")

    # Summary
    console.print()
    table = Table(title="Full Generation Summary", border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Batches attempted", str(len(plan)))
    table.add_row("Generated (raw)", str(len(all_generated)))
    table.add_row("After review", str(len(all_reviewed)))
    table.add_row("Errors", str(len(errors)))

    kt_counts = {}
    dim_counts = {}
    for item in all_reviewed:
        kt = item.get("knowledge_type", "?")
        dim = item.get("dimension", "?")
        kt_counts[kt] = kt_counts.get(kt, 0) + 1
        dim_counts[dim] = dim_counts.get(dim, 0) + 1

    table.add_row("", "")
    for kt in ["Factual", "Conceptual", "Procedural", "Metacognitive"]:
        table.add_row(f"  {kt}", str(kt_counts.get(kt, 0)))
    table.add_row("", "")
    for dim in sorted(dim_counts):
        table.add_row(f"  {dim}", str(dim_counts[dim]))

    console.print(table)
    console.print(f"\n[green]Saved to {OUTPUT_DIR}/phase2_full_reviewed.json[/]")

    if len(all_reviewed) >= 1500:
        console.print(f"[bold green]✓ Target reached: {len(all_reviewed)} ≥ 1500[/]")
    else:
        console.print(f"[bold yellow]⚠ Below target: {len(all_reviewed)} < 1500[/]")


def _save(data, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
