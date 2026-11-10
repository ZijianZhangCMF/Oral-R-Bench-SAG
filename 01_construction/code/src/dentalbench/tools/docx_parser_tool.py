"""DocxParserTool — Parse Chinese dental exam .docx files into structured JSON."""

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class DocxParserInput(BaseModel):
    file_path: str = Field(..., description="Absolute path to the .docx file to parse.")


class DocxParserTool(BaseTool):
    name: str = "docx_parser"
    description: str = (
        "Parse a Chinese dental licensing exam .docx file and extract questions "
        "with options, correct answers, and explanations as structured JSON."
    )
    args_schema: Type[BaseModel] = DocxParserInput

    def _run(self, file_path: str) -> str:
        try:
            from docx import Document
        except ImportError:
            return json.dumps({"error": "python-docx not installed. Run: uv add python-docx"})

        try:
            doc = Document(file_path)
        except Exception as e:
            return json.dumps({"error": f"Failed to open {file_path}: {e}"})

        full_text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
        questions = self._parse_questions(full_text)
        return json.dumps(questions, ensure_ascii=False, indent=2)

    @staticmethod
    def _parse_questions(text: str) -> list[dict]:
        import re

        blocks: list[dict] = []
        # Split on question number patterns like "1." "2." "123."
        parts = re.split(r"\n(?=\d{1,4}[\.\、])", text)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Extract question number
            m = re.match(r"(\d{1,4})[\.\、]\s*(.*)", part, re.DOTALL)
            if not m:
                continue

            q_num = m.group(1)
            body = m.group(2)

            # Extract options (A-E patterns)
            options: dict[str, str] = {}
            option_pattern = re.compile(r"([A-E])[\.\、\s]\s*(.+?)(?=(?:[A-E][\.\、\s])|$)", re.DOTALL)
            for om in option_pattern.finditer(body):
                options[om.group(1)] = om.group(2).strip()

            # Question stem is everything before the first option
            stem = body
            first_opt = re.search(r"[A-E][\.\、\s]", body)
            if first_opt:
                stem = body[: first_opt.start()].strip()

            blocks.append({
                "question_number": int(q_num),
                "question_stem": stem,
                "options": options,
                "raw_text": part,
            })

        return blocks
