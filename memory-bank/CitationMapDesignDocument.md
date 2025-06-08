# CitationMap – Design Document

## 1 Project Overview

**Goal** Build a reproducible, Python‑based toolkit that transforms an author’s publication record into objective, field‑normalized evidence of “original scientific contributions **of major significance**” suitable for an EB‑1A / O‑1 petition or RFE response.

The software must:

* Collect citation and downstream‑uptake data from independent, verifiable sources.
* Quantify impact relative to field norms (percentiles, RCR, etc.).
* Distinguish independent vs. self‑citations and unaffiliated adopters.
* Output lawyer‑ready exhibits (CSV, PDF dashboard, interactive map) with a clear audit trail.

## 2 Stakeholders & Roles

| Stakeholder                  | Responsibility                                                 |
| ---------------------------- | -------------------------------------------------------------- |
| **Applicant** (primary user) | Runs the tool, supplies Scholar ID / DOI list, reviews outputs |
| **Immigration counsel**      | Consumes dashboards/CSVs, selects exhibits for filing          |
| **Developer** (you)          | Designs, codes, tests, documents                               |
| External APIs                | Provide citation & uptake data (OpenAlex, iCite, Lens, etc.)   |

## 3 Functional Requirements

1. **Data Acquisition**

   * Pull publication metadata by Google Scholar ID *and/or* DOI/PMID list.
   * Query OpenAlex for full citation graph and field‑of‑study tags.
   * Retrieve NIH iCite metrics (RCR, percentile).
   * Collect patent citations (Lens.org or PatentsView).
   * Search ClinicalTrials.gov and FDA guidance PDFs for title/DOI mentions.
2. **Impact Analysis**

   * Compute raw & field‑normalized citation counts.
   * Flag top‑10 % / top‑1 % papers in field.
   * Identify independent vs. self citations (author & institution level).
3. **Downstream Uptake Analysis**

   * Aggregate patent, clinical‑trial, guideline, and commercial catalogue mentions.
4. **Visualization & Reporting**

   * Interactive Folium map of unaffiliated citing institutions.
   * Streamlit / Plotly dashboard summarising metrics.
   * Single‑page PDF report per USCIS criterion, plus CSV appendix.
5. **CLI Interface**

   * `citationmap analyze <ScholarID|doi_list.txt> [options]` executes full pipeline.
6. **Configuration**

   * `.env` or `config.toml` for API keys, rate‑limit parameters.

## 4 Non‑Functional Requirements

* **Reproducibility** – deterministic runs; cache raw API responses.
* **Performance** – full run ≤ 15 min for ≤ 500 papers.
* **Extensibility** – modular, test‑covered codebase.
* **Compliance** – respect API ToS and privacy of unpublished data.

## 5 System Architecture

```text
+-------------+        +---------------+        +----------------+
|  CLI / UI   |  -->   |  Pipeline      |  -->   | Reports & Data |
| (Typer /    |        |  Orchestrator  |        |  (HTML / PDF)  |
| Streamlit)  |        |  (async tasks) |        +----------------+
+-------------+        |     |   |      |                ↑
        ↑              |     |   |      |                |
        |          +---v-----v---v----+ |       +--------+--------+
        |          |  Data Acquisition |----->  |  Raw API cache  |
        |          +---+---------+----+         +-----------------+
        |              |         |
        |         +----v--+  +---v----+
        |         | Open  |  |  iCite |
        |         | Alex  |  |        |  etc.
```

### Key Components

| Package                       | Purpose                                                            |
| ----------------------------- | ------------------------------------------------------------------ |
| `data_acquisition/`           | Thin wrappers for each API (OpenAlex, iCite, Lens, ClinicalTrials) |
| `analysis/field_norm.py`      | Computes percentiles, RCR aggregation                              |
| `analysis/independence.py`    | Self‑ vs independent citation logic                                |
| `analysis/uptake.py`          | Patent / clinical trial matching                                   |
| `visualization/maps.py`       | Generates Folium + Choropleth                                      |
| `visualization/dashboards.py` | Streamlit page & PDF export                                        |
| `cli/citationmap.py`          | Typer entry‑point                                                  |

## 6 Technology Stack

| Layer         | Choice                          | Rationale                             |
| ------------- | ------------------------------- | ------------------------------------- |
| Language      | Python 3.11                     | Async support, rich ecosystem         |
| HTTP client   | `httpx`                         | Async; integrates with `asyncio`      |
| Data handling | `pandas`, `polars`              | Transform & merge large tables        |
| Caching       | `diskcache`                     | Simple file‑based cache of API JSON   |
| Visualization | `folium`, `plotly`, `streamlit` | Maps + interactive dashboards         |
| PDF export    | `weasyprint` or `pdfkit`        | Browser‑quality PDF of Streamlit page |
| CLI           | `Typer`                         | User‑friendly commands                |
| Testing       | `pytest`, `vcr.py`              | Cache HTTP fixtures                   |
| CI            | GitHub Actions                  | lint, tests, build Docker image       |

## 7 Data Flow

1. **Input** Scholar ID / DOI list →
2. **OpenAlex** fetch → JSON
3. **iCite** fetch RCR → merge by PMID
4. **Lens** fetch patent cites → merge by DOI
5. **Independence filter** drop self cites
6. **Analysis** compute metrics & percentiles
7. **Visualization** maps, charts
8. **Export** CSV, JSON, PDF, HTML

## 8 Security & Privacy

* Store API keys only in `.env`; never commit.
* Respect robots.txt and rate‑limit headers.
* Cache only public metadata; no personal data beyond author names.

## 9 Testing Strategy

* Unit tests per module with 80 %+ coverage.
* **vcr.py** to record API interactions and ensure deterministic tests.
* End‑to‑end test with a public demo Scholar ID.

## 10 Deployment & Usage Scenarios

* **Local** – pip install + CLI.
* **Docker** – pre‑built image with Chrome headless for PDF export.
* **Streamlit Cloud or internal server** (optional) for interactive use.

## 11 Timeline & Milestones

| Week | Deliverable                                 |
| ---- | ------------------------------------------- |
| 1    | OpenAlex & iCite wrappers + raw data cache  |
| 2    | Field‑norm calculator, independence checker |
| 3    | Patent & clinical‑trial uptake module       |
| 4    | CLI orchestration, Folium map               |
| 5    | Streamlit dashboard + PDF export            |
| 6    | Docs, unit tests, lawyer feedback iteration |

## 12 Risks & Mitigations

| Risk                        | Likelihood | Impact | Mitigation                  |
| --------------------------- | ---------- | ------ | --------------------------- |
| API rate limiting           | Med        | High   | Async back‑off, caching     |
| API deprecation             | Low        | Med    | Interface abstraction layer |
| Patent data noise           | Med        | Med    | Manual validation sampling  |
| USCIS metric interpretation | Med        | High   | Get early counsel feedback  |

## 13 Future Enhancements

* Altmetric / PlumX integration for policy & media mentions.
* ORCID sync to pull author identity automatically.
* Web dashboard to generate exhibits per USCIS criterion “checkbox”.

## 14 Appendix A – Primary External APIs

| API / Dataset      | Endpoint / Library                  | Key Fields Used                                 |
| ------------------ | ----------------------------------- | ----------------------------------------------- |
| OpenAlex           | `https://api.openalex.org/works`    | citations\_count, fields\_of\_study, authorship |
| NIH iCite          | `https://icite.od.nih.gov/api/pubs` | RCR, FCR, year, field percentile                |
| Lens.org Patent    | GraphQL                             | patent\_citations, assignees                    |
| ClinicalTrials.gov | REST searches                       | trial ID, sponsor, reference DOI                |
| Google Geocoding   | `geopy` wrapper                     | lat/long for institution names                  |

---

*Version 0.1 – 08 Jun 2025*
