#!/usr/bin/env python
"""PubMed Case Report Retrieval — Concurrent version with clear progress bars.

Uses ThreadPoolExecutor for parallel full-text fetching (10 workers).
"""

import json
import os
import time
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus
from urllib.request import urlopen, Request

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

OUTPUT_DIR = "./data/raw/case_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL = "oralbench@research.edu"
FULLTEXT_WORKERS = 10  # Concurrent full-text fetchers (NCBI allows 3/sec without key, 10/sec with key)

# ── Subspecialty queries (same as before) ──────────────────────────────────

SUBSPECIALTY_QUERIES = {
    "Operative Dentistry & Endodontics": (
        '("Dental Pulp Diseases"[MeSH] OR "Root Canal Therapy"[MeSH] OR '
        '"Periapical Diseases"[MeSH] OR "Dental Caries"[MeSH] OR '
        '"Tooth Fractures"[MeSH] OR "Endodontics"[MeSH] OR "Pulpitis"[MeSH] OR '
        '"Periapical Abscess"[MeSH] OR "Tooth Resorption"[MeSH])'
    ),
    "Periodontology": (
        '("Periodontal Diseases"[MeSH] OR "Periodontitis"[MeSH] OR '
        '"Gingivitis"[MeSH] OR "Gingival Recession"[MeSH] OR '
        '"Alveolar Bone Loss"[MeSH] OR "Peri-Implantitis"[MeSH])'
    ),
    "Oral & Maxillofacial Surgery": (
        '("Surgery, Oral"[MeSH] OR "Mandibular Fractures"[MeSH] OR '
        '"Orthognathic Surgery"[MeSH] OR "Bisphosphonate-Associated Osteonecrosis of the Jaw"[MeSH] OR '
        '"Cleft Palate"[MeSH] OR "Odontogenic Infections"[MeSH] OR '
        '"Jaw Fractures"[MeSH] OR "Salivary Gland Diseases"[MeSH] OR '
        '"Temporomandibular Joint Disorders"[MeSH])'
    ),
    "Prosthodontics": (
        '("Prosthodontics"[MeSH] OR "Dental Prosthesis"[MeSH] OR '
        '"Crowns"[MeSH] OR "Dental Prosthesis, Implant-Supported"[MeSH] OR '
        '"Maxillofacial Prosthesis"[MeSH] OR "Jaw, Edentulous"[MeSH])'
    ),
    "Orthodontics": (
        '("Orthodontics"[MeSH] OR "Malocclusion"[MeSH] OR '
        '"Tooth Movement Techniques"[MeSH] OR "Orthodontic Appliances"[MeSH] OR '
        '"Palatal Expansion Technique"[MeSH])'
    ),
    "Pediatric Dentistry": (
        '("Pediatric Dentistry"[MeSH] OR "Tooth, Deciduous"[MeSH] OR '
        '"Dental Care for Children"[MeSH] OR "Tooth, Supernumerary"[MeSH] OR '
        '"Amelogenesis Imperfecta"[MeSH] OR "Dentinogenesis Imperfecta"[MeSH])'
    ),
    "Oral Medicine": (
        '("Mouth Diseases"[MeSH] OR "Lichen Planus, Oral"[MeSH] OR '
        '"Candidiasis, Oral"[MeSH] OR "Leukoplakia, Oral"[MeSH] OR '
        '"Pemphigus"[MeSH] OR "Burning Mouth Syndrome"[MeSH] OR '
        '"Sjogren Syndrome"[MeSH] OR "Xerostomia"[MeSH])'
    ),
    "Implantology": (
        '("Dental Implants"[MeSH] OR "Dental Implantation"[MeSH] OR '
        '"Sinus Floor Augmentation"[MeSH] OR "Alveolar Ridge Augmentation"[MeSH] OR '
        '"Osseointegration"[MeSH])'
    ),
    "Preventive Dentistry": (
        '("Preventive Dentistry"[MeSH] OR "Pit and Fissure Sealants"[MeSH] OR '
        '"Fluorides, Topical"[MeSH] OR "Oral Hygiene"[MeSH])'
    ),
    "Basic Oral Sciences": (
        '("Ameloblastoma"[MeSH] OR "Odontogenic Tumors"[MeSH] OR '
        '"Jaw Cysts"[MeSH] OR "Odontogenic Cysts"[MeSH] OR '
        '"Giant Cell Granuloma"[MeSH] OR "Mouth Neoplasms"[MeSH])'
    ),
}


# ── NCBI helpers ───────────────────────────────────────────────────────────

def _fetch_url(url: str, timeout: int = 30) -> bytes | None:
    try:
        req = Request(url, headers={"User-Agent": "OralBench/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def esearch(query: str, retmax: int = 200) -> list[str]:
    full_query = (
        f'{query} AND ("case reports"[Publication Type]) '
        f'AND ("open access"[Filter]) AND ("english"[Language]) '
        f'AND ("2021/01/01"[PDAT] : "2026/12/31"[PDAT])'
    )
    url = (
        f"{ENTREZ_BASE}/esearch.fcgi?db=pmc&term={quote_plus(full_query)}"
        f"&retmax={retmax}&retmode=json&email={EMAIL}"
    )
    data = _fetch_url(url)
    if data:
        return json.loads(data).get("esearchresult", {}).get("idlist", [])
    return []


def efetch_summaries(pmc_ids: list[str]) -> list[dict]:
    if not pmc_ids:
        return []
    url = (
        f"{ENTREZ_BASE}/esummary.fcgi?db=pmc&id={','.join(pmc_ids)}"
        f"&retmode=json&email={EMAIL}"
    )
    data = _fetch_url(url, timeout=30)
    if not data:
        return []

    results = json.loads(data).get("result", {})
    articles = []
    for pid in pmc_ids:
        info = results.get(pid, {})
        if not info or isinstance(info, str):
            continue
        authors_list = info.get("authors", [])
        authors = ", ".join(a.get("name", "") for a in authors_list[:5])
        if len(authors_list) > 5:
            authors += " et al."
        doi = ""
        for aid in info.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
                break
        articles.append({
            "pmcid": f"PMC{pid}",
            "title": info.get("title", ""),
            "authors": authors,
            "journal": info.get("fulljournalname", "") or info.get("source", ""),
            "year": info.get("pubdate", "")[:4],
            "doi": doi,
        })
    return articles


def fetch_and_parse_fulltext(pmc_id: str) -> dict:
    """Fetch full text XML and extract sections. Thread-safe."""
    url = (
        f"{ENTREZ_BASE}/efetch.fcgi?db=pmc&id={pmc_id}"
        f"&rettype=xml&email={EMAIL}"
    )
    sections = {"abstract": "", "case_presentation": "", "discussion": "", "has_fulltext": False}

    data = _fetch_url(url, timeout=45)
    if not data:
        return sections

    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return sections

    sections["has_fulltext"] = True

    for abstract in root.iter("abstract"):
        sections["abstract"] = " ".join(abstract.itertext()).strip()[:2000]
        break

    for sec in root.iter("sec"):
        title_el = sec.find("title")
        title = (title_el.text or "").strip().lower() if title_el is not None else ""
        text = " ".join(sec.itertext()).strip()

        if any(kw in title for kw in ["case report", "case presentation", "case description", "clinical report"]):
            sections["case_presentation"] = text[:5000]
        elif "discussion" in title and not sections["discussion"]:
            sections["discussion"] = text[:3000]

    return sections


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    console.print(Panel.fit(
        "[bold cyan]OralBench — PubMed Case Report Retrieval (Concurrent)[/]\n"
        f"Target: 700-1000 case reports | {len(SUBSPECIALTY_QUERIES)} subspecialties | {FULLTEXT_WORKERS} workers",
        border_style="cyan",
    ))

    all_articles = {}

    # ── Phase 1: Search ────────────────────────────────────────────────────
    console.print("\n[bold]Phase 1: Searching PMC...[/]\n")

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}", justify="left"),
        BarColumn(bar_width=30), MofNCompleteColumn(), TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Searching", total=len(SUBSPECIALTY_QUERIES))

        for subspecialty, query in SUBSPECIALTY_QUERIES.items():
            progress.update(task, description=f"[cyan]{subspecialty[:35]}...")
            pmc_ids = esearch(query, retmax=150)
            time.sleep(0.35)

            for pid in pmc_ids:
                key = f"PMC{pid}"
                if key not in all_articles:
                    all_articles[key] = {"pmcid": key, "subspecialty": [subspecialty], "_raw_id": pid}
                elif subspecialty not in all_articles[key]["subspecialty"]:
                    all_articles[key]["subspecialty"].append(subspecialty)

            progress.update(task, advance=1, description=f"[green]✓ {subspecialty[:30]}[/] ({len(pmc_ids)})")

    console.print(f"  Unique articles found: [bold]{len(all_articles)}[/]")

    # ── Phase 2: Metadata (batched) ────────────────────────────────────────
    console.print("\n[bold]Phase 2: Fetching metadata...[/]\n")

    pmc_ids_list = [a["_raw_id"] for a in all_articles.values()]
    batch_size = 100

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}", justify="left"),
        BarColumn(bar_width=30), MofNCompleteColumn(), TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Metadata", total=len(pmc_ids_list))

        for i in range(0, len(pmc_ids_list), batch_size):
            batch = pmc_ids_list[i:i + batch_size]
            summaries = efetch_summaries(batch)
            for s in summaries:
                if s["pmcid"] in all_articles:
                    all_articles[s["pmcid"]].update(s)
            progress.update(task, advance=len(batch))
            time.sleep(0.35)

    articles_with_meta = [a for a in all_articles.values() if a.get("title")]
    console.print(f"  With metadata: [bold]{len(articles_with_meta)}[/]")

    # ── Phase 3: Full text (concurrent) ────────────────────────────────────
    console.print(f"\n[bold]Phase 3: Fetching full text ({FULLTEXT_WORKERS} concurrent workers)...[/]\n")

    fetched = 0
    failed = 0

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}", justify="left"),
        BarColumn(bar_width=30), MofNCompleteColumn(), TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Full text", total=len(articles_with_meta))

        with ThreadPoolExecutor(max_workers=FULLTEXT_WORKERS) as executor:
            future_to_article = {}
            for article in articles_with_meta:
                raw_id = article.get("_raw_id", article["pmcid"].replace("PMC", ""))
                future = executor.submit(fetch_and_parse_fulltext, raw_id)
                future_to_article[future] = article

            for future in as_completed(future_to_article):
                article = future_to_article[future]
                try:
                    sections = future.result()
                    article.update(sections)
                    if sections.get("has_fulltext"):
                        fetched += 1
                    else:
                        failed += 1
                except Exception:
                    article["has_fulltext"] = False
                    failed += 1

                progress.update(task, advance=1,
                    description=f"[cyan]Full text[/] ✅{fetched} ❌{failed}")

    console.print(f"  Fetched: [bold green]{fetched}[/] | Failed: [bold red]{failed}[/]")

    # ── Save ───────────────────────────────────────────────────────────────
    final_articles = []
    for a in all_articles.values():
        a.pop("_raw_id", None)
        if a.get("title"):
            final_articles.append(a)

    out_path = os.path.join(OUTPUT_DIR, "case_reports_all.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_articles, f, ensure_ascii=False, indent=2)

    manifest = [{
        "pmcid": a["pmcid"], "title": a.get("title", ""), "journal": a.get("journal", ""),
        "year": a.get("year", ""), "doi": a.get("doi", ""),
        "subspecialty": a.get("subspecialty", []),
        "has_fulltext": a.get("has_fulltext", False),
        "has_case_presentation": bool(a.get("case_presentation")),
    } for a in final_articles]

    manifest_path = os.path.join(OUTPUT_DIR, "case_reports_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # ── Summary table ──────────────────────────────────────────────────────
    console.print()
    table = Table(title="Retrieval Summary", border_style="cyan")
    table.add_column("Subspecialty", style="bold", max_width=35)
    table.add_column("Total", justify="right")
    table.add_column("Full Text", justify="right")
    table.add_column("Case Section", justify="right")

    for subspec in SUBSPECIALTY_QUERIES:
        sub_articles = [a for a in final_articles if subspec in a.get("subspecialty", [])]
        ft = sum(1 for a in sub_articles if a.get("has_fulltext"))
        cs = sum(1 for a in sub_articles if a.get("case_presentation"))
        table.add_row(subspec[:35], str(len(sub_articles)), str(ft), str(cs))

    ft_total = sum(1 for a in final_articles if a.get("has_fulltext"))
    cs_total = sum(1 for a in final_articles if a.get("case_presentation"))
    table.add_row("[bold]Total (dedup)[/]", f"[bold]{len(final_articles)}[/]",
                  f"[bold]{ft_total}[/]", f"[bold]{cs_total}[/]", style="bold")
    console.print(table)

    console.print(f"\n[green]Saved to {out_path}[/]")
    if len(final_articles) >= 700:
        console.print(f"[bold green]✓ Target reached: {len(final_articles)} ≥ 700[/]")
    else:
        console.print(f"[bold yellow]⚠ Below target: {len(final_articles)} < 700[/]")


if __name__ == "__main__":
    main()
