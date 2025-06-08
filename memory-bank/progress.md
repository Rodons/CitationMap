# CitationMap - Implementation Progress

*Last Updated: 2025-01-08*

## Phase 0 · Project Setup (Day 1-2) ✅ **COMPLETED**

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 0.1 | ✅ **DONE** | GitHub repo + CI badge | Repository created, CI pipeline, requirements files |
| 0.2 | ✅ **DONE** | Base config | config.toml and env.template created |
| 0.3 | ✅ **DONE** | Auto-format & type checks | Pre-commit hooks installed and configured |

## Phase 1 · Data Acquisition (Week 1) ✅ **COMPLETED**

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 1.1 | ✅ **DONE** | `openalex.py` + tests | OpenAlex wrapper with async, pagination, caching |
| 1.2 | ✅ **DONE** | `icite.py` | iCite API client for RCR, percentiles |
| 1.3 | ✅ **DONE** | `scholar.py` | Google Scholar scraper (fallback) |
| 1.4 | ✅ **DONE** | `patents.py` | Patent client stub (Lens/PatentsView) |
| 1.5 | ✅ **DONE** | `trials.py` | Clinical trials client stub |
| 1.6 | ✅ **DONE** | `cache.py` | Disk-cache abstraction with expiration |
| 1.7 | ✅ **DONE** | Comprehensive tests | Tests for all data acquisition modules |

## Phase 2 · Core Analysis (Week 2-3) ✅ **COMPLETED**

| Task | Status | Output | Notes |
|------|--------|--------|-------|
| 2.1 | ✅ **DONE** | `merger.py` | Merge pipelines → canonical dataframe |
| 2.2 | ✅ **DONE** | `field_norm.py` | Field-normalised metric calculator |
| 2.3 | ✅ **DONE** | `independence.py` | Self vs independent citation classifier |
| 2.4 | ✅ **DONE** | `uptake.py` | Downstream uptake aggregator |
| 2.5 | ✅ **DONE** | pytest suite | Unit tests for analysis modules |

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

**Phase 1 - Data Acquisition**: ✅ COMPLETED
**Phase 2 - Core Analysis**: ✅ COMPLETED
**Next: Phase 3 - Visualization & Reporting**: Implement interactive maps, charts, dashboards, and CLI.

## Notes

- Repository initialized and pushed to https://github.com/Rodons/CitationMap.git
- Core data models implemented with Pydantic for type safety
- Basic package structure established following src/ layout
- **Phase 2 Analysis modules completed:**
  - DataMerger: Converts papers to pandas/polars DataFrames, merges API data, creates analysis summaries
  - FieldNormalizer: RCR percentile calculation, field impact scoring, outlier detection, cross-field ranking
  - IndependenceClassifier: Author/institution name matching, self-citation detection, collaboration analysis
  - UptakeAggregator: Patent citation analysis, clinical trial tracking, translational impact scoring
