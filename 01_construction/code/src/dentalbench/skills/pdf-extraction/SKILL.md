---
name: pdf-extraction
description: Extract structured content from medical textbook and clinical guideline PDFs into hierarchical JSON. Use when ingesting source material for QA generation or taxonomy classification.
metadata:
  author: OralBench Team
  version: "2.0.0"
---

# PDF Extraction

## Input

Accept text-based PDF files of oral medicine textbooks or clinical guidelines.

Do NOT attempt OCR. Do NOT process scanned-image PDFs. Reject any PDF without an extractable text layer.

## Output Schema

Produce one JSON object per PDF with this structure:

```json
{
  "source": {
    "filename": "oral_medicine_8th_ed.pdf",
    "title": "Oral Medicine: Diagnosis and Treatment",
    "authors": ["Author A", "Author B"],
    "edition": "8th",
    "year": 2022,
    "total_pages": 542
  },
  "chapters": [
    {
      "chapter_number": 5,
      "title": "Oral Mucosal Diseases",
      "page_start": 78,
      "page_end": 134,
      "sections": [
        {
          "id": "ch5-s1",
          "heading": "Recurrent Aphthous Stomatitis",
          "level": 1,
          "page_number": 80,
          "content_blocks": [
            {
              "content_type": "text",
              "title": "Recurrent Aphthous Stomatitis",
              "section_hierarchy": ["Chapter 5: Oral Mucosal Diseases", "Recurrent Aphthous Stomatitis"],
              "content": "Recurrent aphthous stomatitis (RAS) is the most common...",
              "page_number": 80
            }
          ],
          "subsections": []
        }
      ]
    }
  ],
  "references": []
}
```

Every content block MUST include these fields:
- `title` — heading of the enclosing section
- `section_hierarchy` — ordered list from chapter down to current heading
- `content` — the extracted text
- `page_number` — source page
- `content_type` — one of: `"text"`, `"table"`, `"list"`

## Extraction Procedure

### 1. Detect Document Structure

1. Extract book-level metadata: title, authors, edition, publisher, year, ISBN.
2. Identify chapter boundaries using font-size changes, bold formatting, numbering prefixes, or centered/all-caps text.
3. Within each chapter, detect section headings at up to 4 depth levels (H1–H4). Use these heuristics:
   - Font size larger than body text indicates a heading.
   - Numbered prefixes like `3.2.1` indicate subsection depth.
   - Lines under 80 characters followed by body text are likely headings.
4. Map every content block to its source page number.

### 2. Extract Content Blocks

Process each section in reading order. For each block, assign the correct `content_type`:

- `"text"` — paragraph text. Preserve paragraph boundaries. Do NOT merge paragraphs separated by whitespace.
- `"table"` — structured tabular data. Extract caption, column headers as an array, and each row as an object keyed by column header. If a table spans multiple pages, merge into one table and note the page range.
- `"list"` — bulleted or numbered lists. Preserve nesting structure.

For clinical callout boxes or definitions, set `content_type: "text"` and prepend `[CALLOUT]` or `[DEFINITION]` to the content string.

### 3. Handle Figures

Extract figure captions and labels (e.g., "Figure 3-2. Leukoplakia of the buccal mucosa"). Record page number. Set `content_type: "text"` and prepend `[FIGURE_CAPTION]`.

Do NOT extract image pixel data. Do NOT attempt to describe image contents.

### 4. Extract References

Parse the bibliography section. For each reference, extract: `authors`, `title`, `journal`, `year`, `volume`, `pages`, `doi`. If a reference cannot be fully parsed, store raw text in a `raw` field.

### 5. Strip Noise

Remove before output:
- Page headers and footers
- Watermarks
- Page numbers embedded in running text
- Publisher logos or copyright notices repeated on each page

Do NOT remove footnotes — include them as `content_type: "text"` blocks with `[FOOTNOTE]` prefix.

## Validation Rules

After extraction, run these checks. Fail the extraction if any critical check fails.

1. Every page in the source PDF must map to at least one content block. Log gaps as warnings.
2. Heading levels must nest monotonically — no H3 directly under H1 without H2.
3. Every table row must have the same column count as the header array.
4. Page numbers in content blocks must be non-decreasing within a chapter.
5. Output must be valid UTF-8. Verify Chinese characters, medical symbols, and diacritics are preserved.

## Error Handling

- If a page yields no extractable text, log `{"extraction_error": true, "page": N}` and continue.
- If a table cannot be parsed structurally, store as `content_type: "text"` with raw table text and add `"parse_warning": "table_fallback"`.
- When heading detection is ambiguous, prefer over-splitting (more sections) over under-splitting.

## Constraints

- Do NOT extract images or image data.
- Do NOT include page headers, footers, or watermarks in output.
- Do NOT attempt OCR on image-only pages.
- Do NOT merge content from different sections into a single block.
- Process one chapter at a time to manage memory on large textbooks.
