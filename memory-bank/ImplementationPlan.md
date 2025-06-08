# CitationMap – Implementation Plan

*Version 0.1 – 08 Jun 2025*

---

## Overview

This document breaks the project into concrete, time‑boxed tasks. Phases can overlap where dependencies allow; durations assume \~50 % developer allocation.

---

### Phase 0 · Project Setup (Day 1‑2)

|  #   | Task                                                    | Output                    |
| ---- | ------------------------------------------------------- | ------------------------- |
|  0.1 | Repository skeleton, CI pipeline, `pip‑tools` lockfiles | GitHub repo + CI badge    |
|  0.2 | `config.toml` and `.env.template`                       | Base config               |
|  0.3 | Pre‑commit hooks (black, isort, flake8, mypy)           | Auto‑format & type checks |

### Phase 1 · Data Acquisition (Week 1)

|  #   | Task                                              | Depends | Output                |
| ---- | ------------------------------------------------- | ------- | --------------------- |
|  1.1 | **OpenAlex wrapper** (async, pagination, caching) | 0.x     | `openalex.py` + tests |
|  1.2 | **iCite API client** (RCR, percentiles)           | 0.x     | `icite.py`            |
|  1.3 | Google Scholar scraper (fallback)                 | 0.x     | `scholar.py`          |
|  1.4 | Lens / PatentsView client → patent citations      | 1.1     | `patents.py`          |
|  1.5 | ClinicalTrials.gov search utility                 | 1.1     | `trials.py`           |
|  1.6 | Disk‑cache abstraction layer                      | 0.x     | `cache.py`            |
|  1.7 | vcr.py fixtures for each API                      | 1.x     | Deterministic tests   |

### Phase 2 · Core Analysis (Week 2‑3)

|  #   | Task                                                       | Depends     | Output            |
| ---- | ---------------------------------------------------------- | ----------- | ----------------- |
|  2.1 | Merge pipelines → canonical dataframe (`pandas→polars`)    | 1.x         | `merger.py`       |
|  2.2 | Field‑normalised metric calculator (RCR, percentiles)      | 2.1         | `field_norm.py`   |
|  2.3 | Self‑ vs independent citation classifier                   | 2.1         | `independence.py` |
|  2.4 | Downstream uptake aggregator (patents, trials, guidelines) | 2.1,1.4‑1.5 | `uptake.py`       |
|  2.5 | Unit tests for analysis modules                            | 2.x         | pytest suite      |

### Phase 3 · Visualisation & Reporting (Week 3‑4)

|  #   | Task                                                    | Depends     | Output                  |
| ---- | ------------------------------------------------------- | ----------- | ----------------------- |
|  3.1 | Folium map factory (geo‑resolution, clustering)         | 2.x         | `maps.py` + HTML        |
|  3.2 | Plotly charts (time‑series, bar)                        | 2.x         | `charts.py`             |
|  3.3 | Streamlit dashboard (interactive exploration)           | 3.1‑3.2     | `dashboards.py`         |
|  3.4 | PDF export (weasyprint / pdfkit)                        | 3.3         | One‑page lawyer exhibit |
|  3.5 | CLI command `citationmap analyze` orchestrates full run | 0.1,2.x,3.x | Typer CLI               |
|  3.6 | Dockerfile inc. headless Chrome                         | 3.5         | `docker/`               |

### Phase 4 · Quality, Docs & Release v0.1 (Week 5‑6)

|  #   | Task                                          | Depends   | Output            |
| ---- | --------------------------------------------- | --------- | ----------------- |
|  4.1 | 80 %+ test coverage, mutation tests           | All prior | Coverage report   |
|  4.2 | Sphinx / MkDocs documentation                 | All prior | docs site         |
|  4.3 | Example notebook & sample outputs             | 3.x       | `examples/`       |
|  4.4 | Lawyer feedback loop; tweak metrics / wording | 3.4       | Revised templates |
|  4.5 | Tag v0.1, push Docker image to GHCR           | 4.x       | Release assets    |

### Phase 5 · Stretch Goals (post‑v0.1)

|  #   | Task                          | Description                       |
| ---- | ----------------------------- | --------------------------------- |
|  5.1 | Altmetric / PlumX integration | Policy, media, guideline mentions |
|  5.2 | ORCID auto‑matching           | Input simplification              |
|  5.3 | Optional SaaS web wrapper     | Multi‑user jobs                   |

---

## Risks & Mitigations

| Risk                      | Likelihood | Impact | Mitigation                  |
| ------------------------- | ---------- | ------ | --------------------------- |
| API rate‑limits / bans    | Medium     | High   | Async back‑off, disk‑cache  |
| API schema changes        | Low        | Medium | Isolate wrappers; CI alerts |
| Patent data noise         | Medium     | Medium | Manual sampling QA          |
| USCIS interpretive shifts | Medium     | High   | Early counsel review        |

## Future Enhancements

* Altmetric & PlumX integration for policy relevance.
* ORCID‑based author identity resolution.
* Web UI with user auth and resumable batch jobs for law‑firm use.

## Appendix A – Key External APIs

| API / Dataset  | Endpoint / Library                  | Fields Used                         |
| -------------- | ----------------------------------- | ----------------------------------- |
| OpenAlex       | `https://api.openalex.org/works`    | citations\_count, fields\_of\_study |
| NIH iCite      | `https://icite.od.nih.gov/api/pubs` | RCR, FCR, percentiles               |
| Lens / Patents | GraphQL                             | patent\_citations, assignees        |
| ClinicalTrials | REST search                         | trial ID, sponsor, refs             |
| Google Geocode | `geopy` wrapper                     | lat/long                            |
