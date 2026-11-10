---
name: web-research-medical
description: Fetch supplementary clinical information from authoritative medical sources and return structured summaries with source authority ratings. Use when existing corpus data needs enrichment with guideline-level evidence or consensus definitions.
metadata:
  author: OralBench Team
  version: "1.0.0"
---

# Web Research — Medical Sources

## Objective

Retrieve supplementary clinical information from authoritative medical sources to enrich OralBench content. Every piece of retrieved information must be traceable to a specific URL and rated for source authority.

## Output Schema

Produce a JSON array of retrieved items:

```json
[
  {
    "url": "https://www.who.int/news-room/fact-sheets/detail/oral-health",
    "source_authority": "tier_1",
    "content_summary": "WHO defines oral health as a state of being free from chronic mouth and facial pain, oral and throat cancer, oral infection and sores...",
    "relevance_score": 0.92
  }
]
```

## Source Authority Tiers

Assign exactly one tier to each source:

| Tier | Label | Sources |
|------|-------|---------|
| `tier_1` | Highest authority | WHO, Cochrane Library, NICE guidelines, UpToDate, national clinical practice guidelines |
| `tier_2` | Professional organizations | ADA, AAE, AAP, AOS, AAOM, AAOMP, IADR, specialty society position papers |
| `tier_3` | Peer-reviewed literature | PubMed-indexed journals, PMC open-access articles, systematic reviews |
| `tier_4` | Educational resources | University dental school resources, established medical education platforms (e.g., StatPearls) |

Do NOT use sources below tier_4. Specifically:
- Do NOT use patient forums, health Q&A sites (e.g., HealthTap, RealSelf), or social media.
- Do NOT use Wikipedia as a primary source. It may be used only to locate primary references, which must then be fetched directly.
- Do NOT use commercial dental product sites, manufacturer marketing materials, or sponsored content.
- Do NOT use blogs, news articles, or press releases as clinical evidence.

## Search Procedure

### 1. Define the Information Need

Before searching, formulate a precise query. Include:
- The specific clinical concept or term to look up
- The context (e.g., "diagnostic criteria for", "treatment guidelines for", "epidemiology of")
- The target subspecialty if relevant

### 2. Select Target Sources

Choose sources in tier priority order. Always check tier_1 sources first. Move to lower tiers only when higher tiers lack the needed information.

Preferred source URLs by type:

| Information Type | Primary Sources |
|-----------------|-----------------|
| Disease definitions & classification | WHO (who.int), ICD-11 (icd.who.int) |
| Treatment guidelines | NICE (nice.org.uk), ADA (ada.org), Cochrane (cochranelibrary.com) |
| Drug information | UpToDate, FDA labels, BNF |
| Epidemiology | WHO Global Oral Health reports, CDC (cdc.gov) |
| Specialty consensus | AAE (aae.org), AAP (perio.org), AOS, AAOM (aaom.com) |
| Evidence summaries | Cochrane (cochranelibrary.com), PubMed systematic reviews |

### 3. Fetch and Extract

For each source:
1. Fetch the page content.
2. Extract only the clinically relevant information. Strip navigation, ads, disclaimers, and boilerplate.
3. Summarize the extracted content in 2–5 sentences in `content_summary`. Preserve specific numbers, criteria, and recommendations verbatim.
4. Record the exact URL (not a search results page).

### 4. Score Relevance

Assign `relevance_score` as a float between 0.0 and 1.0:
- 1.0 — directly answers the query with authoritative, current guidance
- 0.7–0.9 — relevant but partially addresses the query or is slightly dated
- 0.4–0.6 — tangentially related, provides useful context
- Below 0.4 — do NOT include in output

### 5. Validate Currency

Check the publication or last-updated date of each source.
- Prefer sources updated within the last 5 years.
- If a source is older than 5 years, include it only if no newer authoritative source exists, and add `"currency_warning": "last_updated_YYYY"` to the output object.

## Error Handling

- If a URL returns a 404 or is unreachable, log it in an `"unreachable_urls"` array and continue.
- If a source requires authentication (e.g., UpToDate paywall), note `"access": "restricted"` and include only the publicly visible abstract or summary.
- If no authoritative source can be found for a query, return an empty array and add `"no_results_reason": "description"`.

## Constraints

- Do NOT use patient forums, Wikipedia, or commercial dental product sites as primary sources.
- Do NOT fabricate URLs or content summaries.
- Do NOT include sources with `relevance_score` below 0.4.
- Do NOT present marketing claims as clinical evidence.
- Do NOT include more than 10 sources per query — keep the most authoritative and relevant.
- Do NOT modify or editorialize source content in `content_summary` — summarize faithfully.
- Do NOT use sources that are behind a full paywall unless a public abstract is available.
