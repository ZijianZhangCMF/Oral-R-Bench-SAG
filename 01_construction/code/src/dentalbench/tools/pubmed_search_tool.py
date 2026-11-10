"""PubMedSearchTool — Search PMC Open Access for oral medicine case reports."""

import json
import time
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class PubMedSearchInput(BaseModel):
    query: str = Field(..., description="PubMed search query string (MeSH terms or keywords).")
    max_results: int = Field(default=50, description="Maximum number of results to return.")


class PubMedSearchTool(BaseTool):
    name: str = "pubmed_search"
    description: str = (
        "Search PubMed Central Open Access subset for oral medicine case reports. "
        "Use when retrieving clinical case reports for procedural QA generation."
    )
    args_schema: Type[BaseModel] = PubMedSearchInput

    def _run(self, query: str, max_results: int = 50) -> str:
        try:
            from Bio import Entrez
        except ImportError:
            return json.dumps({"error": "biopython not installed. Run: uv add biopython"})

        Entrez.email = "oralbench@example.com"

        # Build query: case reports, open access, last 5 years, English
        full_query = (
            f"({query}) AND (case reports[pt]) AND (open access[filter]) "
            f"AND (english[la]) AND (\"2021\"[PDAT] : \"2026\"[PDAT])"
        )

        try:
            handle = Entrez.esearch(db="pmc", term=full_query, retmax=max_results, sort="relevance")
            results = Entrez.read(handle)
            handle.close()
        except Exception as e:
            return json.dumps({"error": f"ESearch failed: {e}"})

        id_list = results.get("IdList", [])
        if not id_list:
            return json.dumps({"count": 0, "articles": []})

        articles = []
        # Fetch in batches of 50
        for i in range(0, len(id_list), 50):
            batch = id_list[i : i + 50]
            try:
                handle = Entrez.efetch(db="pmc", id=",".join(batch), rettype="xml")
                records = Entrez.read(handle)
                handle.close()
            except Exception as e:
                articles.append({"error": f"EFetch failed for batch {i}: {e}"})
                continue

            for article in records.get("PubmedArticle", records) if isinstance(records, dict) else []:
                parsed = self._parse_article(article)
                if parsed:
                    articles.append(parsed)

            if i + 50 < len(id_list):
                time.sleep(0.4)  # Respect NCBI rate limit

        return json.dumps({"count": len(articles), "articles": articles}, ensure_ascii=False, indent=2)

    @staticmethod
    def _parse_article(article) -> dict | None:
        try:
            if hasattr(article, "get"):
                medline = article.get("MedlineCitation", {})
                art = medline.get("Article", {})
            else:
                return {"pmcid": str(article), "title": "", "authors": "", "journal": "", "year": "", "doi": ""}

            title = str(art.get("ArticleTitle", ""))
            journal = str(art.get("Journal", {}).get("Title", ""))
            year = ""
            pub_date = art.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            if pub_date:
                year = str(pub_date.get("Year", ""))

            authors_list = art.get("AuthorList", [])
            authors = ", ".join(
                f"{a.get('LastName', '')} {a.get('Initials', '')}"
                for a in authors_list[:5]
            )
            if len(authors_list) > 5:
                authors += " et al."

            pmid = str(medline.get("PMID", ""))
            doi = ""
            for eid in art.get("ELocationID", []):
                if str(eid.attributes.get("EIdType", "")) == "doi":
                    doi = str(eid)

            return {
                "pmcid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": year,
                "doi": doi,
            }
        except Exception:
            return None
