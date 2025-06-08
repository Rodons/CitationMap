# CitationMap

[![CI](https://github.com/username/citationmap/workflows/CI/badge.svg)](https://github.com/username/citationmap/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A reproducible, Python-based toolkit that transforms an author's publication record into objective, field-normalized evidence of "original scientific contributions of major significance" suitable for EB-1A / O-1 petition or RFE response.

## Features

- **Data Acquisition**: Collect citation and downstream-uptake data from independent, verifiable sources
- **Impact Analysis**: Quantify impact relative to field norms (percentiles, RCR, etc.)
- **Independence Analysis**: Distinguish independent vs. self-citations and unaffiliated adopters
- **Visualization**: Interactive maps and dashboards of citing institutions
- **Export**: Lawyer-ready exhibits (CSV, PDF dashboard, interactive map) with clear audit trail

## Quick Start

```bash
# Install CitationMap
pip install citationmap

# Run analysis on a Google Scholar ID
citationmap analyze scholar:abc123xyz

# Or analyze from a list of DOIs
citationmap analyze doi_list.txt
```

## Data Sources

- **OpenAlex**: Citation graphs and field-of-study classifications
- **NIH iCite**: RCR metrics and field percentiles
- **Lens.org**: Patent citations
- **ClinicalTrials.gov**: Clinical trial mentions
- **FDA Guidance**: Regulatory document mentions

## Architecture

```
data_acquisition/     # API wrappers (OpenAlex, iCite, Lens, etc.)
analysis/            # Core analysis modules
├── field_norm.py    # Field normalization and percentiles
├── independence.py  # Self vs independent citation logic
└── uptake.py        # Downstream uptake analysis
visualization/       # Maps and dashboards
├── maps.py         # Folium geographic visualizations
└── dashboards.py   # Streamlit interactive dashboards
cli/                # Command-line interface
reports/            # PDF and CSV export utilities
```

## Installation

### From PyPI (Coming Soon)

```bash
pip install citationmap
```

### From Source

```bash
git clone https://github.com/username/citationmap.git
cd citationmap
pip install -e .
```

### Docker

```bash
docker run -it citationmap/citationmap:latest citationmap analyze scholar:abc123xyz
```

## Configuration

Create a `.env` file with your API keys:

```bash
cp .env.template .env
# Edit .env with your API credentials
```

Required API keys:
- `OPENALEX_API_KEY` (optional, for higher rate limits)
- `LENS_API_TOKEN` (for patent data)

## Usage Examples

### CLI Interface

```bash
# Analyze Google Scholar profile
citationmap analyze scholar:abc123xyz

# Analyze specific papers by DOI
citationmap analyze --input-file papers.txt

# Generate only the map visualization
citationmap analyze scholar:abc123xyz --output-types map

# Custom output directory
citationmap analyze scholar:abc123xyz --output-dir ./results
```

### Python API

```python
from citationmap import CitationAnalyzer

analyzer = CitationAnalyzer()
results = analyzer.analyze_scholar_id("abc123xyz")

# Generate visualizations
results.create_map("citation_map.html")
results.create_dashboard("dashboard.html")
results.export_pdf("report.pdf")
```

## Output Formats

- **Interactive Map**: Geographic distribution of citing institutions
- **Dashboard**: Streamlit-based interactive metrics explorer
- **PDF Report**: Lawyer-ready single-page summary per USCIS criterion
- **CSV Data**: Raw data for further analysis

## Development

### Setup

```bash
git clone https://github.com/username/citationmap.git
cd citationmap
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

### Testing

```bash
pytest
pytest --cov=citationmap  # With coverage
```

### Building Documentation

```bash
cd docs
make html
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use CitationMap in your research or legal proceedings, please cite:

```bibtex
@software{citationmap2025,
  title = {CitationMap: Evidence Generation for Immigration Petitions},
  author = {[Author Name]},
  year = {2025},
  url = {https://github.com/username/citationmap}
}
```

## Disclaimer

This tool is designed to assist in gathering and presenting publicly available academic data. It does not provide legal advice. Always consult with qualified immigration counsel for legal matters.

## Support

- 📖 [Documentation](https://citationmap.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/username/citationmap/issues)
- 💬 [Discussions](https://github.com/username/citationmap/discussions) 