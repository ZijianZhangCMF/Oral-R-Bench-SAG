---
name: pubmed-search
description: Search PMC Open Access for oral medicine case reports using NCBI E-utilities and produce structured metadata JSON. Use when building the case report corpus for OralBench.
metadata:
  author: OralBench Team
  version: "1.0.0"
---

# PubMed Search

## Objective

Retrieve 700–1000 open-access oral medicine case reports published in the last 5 years from PubMed Central, balanced across all 10 oral subspecialties.

## Output Schema

Produce a JSON array of case report metadata:

```json
[
  {
    "pmcid": "PMC9876543",
    "title": "Oral Verrucous Carcinoma Mimicking Leukoplakia: A Case Report",
    "authors": ["Smith J", "Doe A", "Zhang L"],
    "journal": "Oral Surgery, Oral Medicine, Oral Pathology and Oral Radiology",
    "year": 2023,
    "doi": "10.1016/j.oooo.2023.01.001",
    "subspecialty_tags": ["S9", "S1"]
  }
]
```

## Search Procedure

### 1. Construct Queries Using NCBI E-utilities

Use the Entrez API endpoints:
- `esearch.fcgi` — to search and retrieve PMCIDs
- `efetch.fcgi` — to fetch article metadata
- `elink.fcgi` — to resolve PMIDs to PMCIDs if needed

Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

Always include an `api_key` if available. Respect NCBI rate limits: 3 requests/second without key, 10 requests/second with key.

### 2. Apply Required Filters

Every query MUST include all of these filters:

```
("case reports"[Publication Type])
AND ("open access"[Filter])
AND ("english"[Language])
AND ("2021/01/01"[Date - Publication] : "3000"[Date - Publication])
AND ("pmc"[Filter])
```

Do NOT include reviews, meta-analyses, systematic reviews, editorials, letters, or commentary articles.

### 3. Search by Subspecialty

Run one query per subspecialty using the curated MeSH terms in `references/mesh-terms.md`. Target 70–100 case reports per subspecialty for balanced coverage.

Query template per subspecialty:

```
(SUBSPECIALTY_MESH_TERMS) AND ("case reports"[Publication Type]) AND ("open access"[Filter]) AND ("english"[Language]) AND ("2021/01/01"[Date - Publication] : "3000"[Date - Publication])
```

Replace `SUBSPECIALTY_MESH_TERMS` with the OR-joined MeSH terms from `references/mesh-terms.md` for that subspecialty.

### 4. Deduplicate

After collecting results from all 10 subspecialty queries:
1. Deduplicate by PMCID.
2. If a case report matches multiple subspecialties, keep it once and assign all matching subspecialty tags.
3. Log the total count per subspecialty after deduplication.

### 5. Extract Metadata

For each unique PMCID, extract:
- `pmcid` — PMC identifier (format: `PMC` followed by digits)
- `title` — article title
- `authors` — list of author names in "Last First" format
- `journal` — journal name
- `year` — publication year
- `doi` — DOI if available, empty string if not
- `subspecialty_tags` — list of matching subspecialty codes (S1–S10)

### 6. Validate Coverage

After collection, check subspecialty distribution:
- Minimum 50 case reports per subspecialty.
- If any subspecialty has fewer than 50, broaden the MeSH terms for that subspecialty and re-query.
- If total exceeds 1000, prioritize more recent publications and trim the oldest from over-represented subspecialties.

## Error Handling

- If the NCBI API returns an error or rate-limit response, wait 1 second and retry up to 3 times.
- If a PMCID cannot be resolved to metadata, log it in an `"unresolved_pmcids"` array and continue.
- If a subspecialty query returns 0 results, log a warning and try alternative MeSH terms from `references/mesh-terms.md`.

## Constraints

- Do NOT include non-case-report article types (reviews, meta-analyses, editorials, letters, commentary).
- Do NOT include non-English articles.
- Do NOT include articles without PMC open-access full text.
- Do NOT include articles published before 2021.
- Do NOT fabricate PMCIDs or metadata — every entry must come from an actual NCBI API response.
- Do NOT exceed 10 API requests per second (or 3 without an API key).
