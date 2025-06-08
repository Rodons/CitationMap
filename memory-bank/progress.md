# CitationMap - Implementation Progress

*Last Updated: 2025-01-08*

## Phase 0 · Project Setup (Day 1-2)

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 0.1 | ✅ **DONE** | GitHub repo + CI badge | Repository created, basic structure pushed to GitHub |
| 0.2 | 🔄 **IN PROGRESS** | Base config | Need to create config.toml and .env.template |
| 0.3 | ⏳ **PENDING** | Auto-format & type checks | Pre-commit hooks setup needed |

## Phase 1 · Data Acquisition (Week 1)

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 1.1 | ⏳ **PENDING** | `openalex.py` + tests | OpenAlex wrapper (async, pagination, caching) |
| 1.2 | ⏳ **PENDING** | `icite.py` | iCite API client (RCR, percentiles) |
| 1.3 | ⏳ **PENDING** | `scholar.py` | Google Scholar scraper (fallback) |
| 1.4 | ⏳ **PENDING** | `patents.py` | Lens / PatentsView client → patent citations |
| 1.5 | ⏳ **PENDING** | `trials.py` | ClinicalTrials.gov search utility |
| 1.6 | ⏳ **PENDING** | `cache.py` | Disk-cache abstraction layer |
| 1.7 | ⏳ **PENDING** | Deterministic tests | vcr.py fixtures for each API |

## Phase 2 · Core Analysis (Week 2-3)

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 2.1 | ⏳ **PENDING** | `merger.py` | Merge pipelines → canonical dataframe |
| 2.2 | ⏳ **PENDING** | `field_norm.py` | Field-normalised metric calculator |
| 2.3 | ⏳ **PENDING** | `independence.py` | Self vs independent citation classifier |
| 2.4 | ⏳ **PENDING** | `uptake.py` | Downstream uptake aggregator |
| 2.5 | ⏳ **PENDING** | pytest suite | Unit tests for analysis modules |

## Phase 3 · Visualisation & Reporting (Week 3-4)

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 3.1 | ⏳ **PENDING** | `maps.py` + HTML | Folium map factory |
| 3.2 | ⏳ **PENDING** | `charts.py` | Plotly charts |
| 3.3 | ⏳ **PENDING** | `dashboards.py` | Streamlit dashboard |
| 3.4 | ⏳ **PENDING** | One-page lawyer exhibit | PDF export |
| 3.5 | ⏳ **PENDING** | Typer CLI | CLI command orchestration |
| 3.6 | ⏳ **PENDING** | `docker/` | Dockerfile inc. headless Chrome |

## Phase 4 · Quality, Docs & Release v0.1 (Week 5-6)

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 4.1 | ⏳ **PENDING** | Coverage report | 80%+ test coverage, mutation tests |
| 4.2 | ⏳ **PENDING** | docs site | Sphinx / MkDocs documentation |
| 4.3 | ⏳ **PENDING** | `examples/` | Example notebook & sample outputs |
| 4.4 | ⏳ **PENDING** | Revised templates | Lawyer feedback loop |
| 4.5 | ⏳ **PENDING** | Release assets | Tag v0.1, push Docker image |

## Current Priority

**Phase 0 - Project Setup**: Completing configuration files and development environment setup.

## Notes

- Repository initialized and pushed to https://github.com/Rodons/CitationMap.git
- Core data models implemented with Pydantic for type safety
- Basic package structure established following src/ layout 