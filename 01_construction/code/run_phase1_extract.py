#!/usr/bin/env python
"""Phase 1: Batch data extraction — PDF text + Exam docx parsing.

Step 1 (this script): Extract raw text from all PDFs and parse all exam docx files.
Step 2 (agent): Classify and structure the extracted content.
"""

import json
import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

PDF_DIR = "./RAG data"
EXAM_DIR = "./执业-系统真题-Word"
OUTPUT_DIR = "./data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_all_pdfs():
    """Extract text from all PDFs using pypdf. Write per-PDF JSON to avoid memory issues."""
    from pypdf import PdfReader

    pdf_dir = Path(PDF_DIR)
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")

    pdf_output_dir = os.path.join(OUTPUT_DIR, "pdfs")
    os.makedirs(pdf_output_dir, exist_ok=True)

    manifest = []
    for i, pdf_path in enumerate(pdf_files):
        print(f"  [{i+1}/{len(pdf_files)}] {pdf_path.name}...", end=" ", flush=True)
        try:
            reader = PdfReader(str(pdf_path))
            pages = []
            total_chars = 0
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                # Remove control characters that break JSON
                text = "".join(c if ord(c) >= 32 or c in "\n\r\t" else " " for c in text)
                text = text.strip()
                if text:
                    pages.append({"page": page_num + 1, "text": text})
                    total_chars += len(text)

            sample = " ".join(p["text"][:200] for p in pages[:3])
            is_chinese = sum(1 for c in sample if '\u4e00' <= c <= '\u9fff') > len(sample) * 0.1
            lang = "zh" if is_chinese else "en"

            name_lower = pdf_path.name.lower()
            if any(kw in name_lower for kw in ["指南", "guideline", "guide", "共识", "consensus"]):
                source_type = "guideline"
            else:
                source_type = "textbook"

            # Save per-PDF file
            safe_name = pdf_path.stem[:80].replace("/", "_")
            per_pdf_path = os.path.join(pdf_output_dir, f"{safe_name}.json")
            entry = {
                "filename": pdf_path.name,
                "source_type": source_type,
                "language": lang,
                "total_pages": len(reader.pages),
                "extracted_pages": len(pages),
                "total_chars": total_chars,
                "pages": pages,
            }
            with open(per_pdf_path, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False)

            manifest.append({
                "filename": pdf_path.name,
                "source_type": source_type,
                "language": lang,
                "total_pages": len(reader.pages),
                "extracted_pages": len(pages),
                "total_chars": total_chars,
                "output_file": per_pdf_path,
            })
            print(f"{len(pages)} pages, {total_chars} chars, {lang}, {source_type}")

        except Exception as e:
            print(f"ERROR: {e}")
            manifest.append({"filename": pdf_path.name, "error": str(e)})

    # Save manifest (lightweight, no page text)
    manifest_path = os.path.join(OUTPUT_DIR, "pdf_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    ok = [r for r in manifest if "error" not in r]
    total_chars = sum(r["total_chars"] for r in ok)
    en_count = sum(1 for r in ok if r["language"] == "en")
    zh_count = sum(1 for r in ok if r["language"] == "zh")
    gl_count = sum(1 for r in ok if r["source_type"] == "guideline")
    tb_count = sum(1 for r in ok if r["source_type"] == "textbook")
    print(f"\nPDF Summary: {len(ok)}/{len(manifest)} OK")
    print(f"  English: {en_count}, Chinese: {zh_count}")
    print(f"  Textbooks: {tb_count}, Guidelines: {gl_count}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Per-PDF files: {pdf_output_dir}/")
    return manifest


def parse_all_exams():
    """Parse all exam docx files."""
    from dentalbench.tools.docx_parser_tool import DocxParserTool

    exam_dir = Path(EXAM_DIR)
    # Find paired files: X-题目.docx and X-解析.docx
    question_files = sorted(exam_dir.glob("*题目*.docx"))
    print(f"\nFound {len(question_files)} exam question files")

    tool = DocxParserTool()
    all_subjects = []

    for qf in question_files:
        subject_name = qf.name.split("、")[1].split("-")[0] if "、" in qf.name else qf.stem
        answer_file = str(qf).replace("题目", "解析")

        print(f"  Parsing: {subject_name}...", end=" ", flush=True)

        # Parse questions
        q_result = json.loads(tool._run(file_path=str(qf)))

        # Parse answers if file exists
        a_result = []
        if os.path.exists(answer_file):
            a_result = json.loads(tool._run(file_path=answer_file))

        # Merge answers into questions by question_number
        answer_map = {a["question_number"]: a for a in a_result}
        for q in q_result:
            ans = answer_map.get(q["question_number"], {})
            q["answer_explanation"] = ans.get("raw_text", "")
            q["subject"] = subject_name

        all_subjects.append({
            "subject": subject_name,
            "question_file": qf.name,
            "answer_file": os.path.basename(answer_file) if os.path.exists(answer_file) else None,
            "question_count": len(q_result),
            "questions": q_result,
        })
        print(f"{len(q_result)} questions")

    out_path = os.path.join(OUTPUT_DIR, "exam_parsed.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_subjects, f, ensure_ascii=False, indent=2)

    total_q = sum(s["question_count"] for s in all_subjects)
    print(f"\nSaved {len(all_subjects)} subjects, {total_q} total questions to {out_path}")
    return all_subjects


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1 — Step 1: Raw Data Extraction")
    print("=" * 60)

    print("\n--- PDF Extraction ---")
    pdfs = extract_all_pdfs()

    print("\n--- Exam Parsing ---")
    exams = parse_all_exams()

    print("\n" + "=" * 60)
    print("Phase 1 Step 1 COMPLETE")
    print(f"Output: {OUTPUT_DIR}/pdf_extracted.json")
    print(f"Output: {OUTPUT_DIR}/exam_parsed.json")
    print("=" * 60)
