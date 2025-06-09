"""
CitationMap: Comprehensive citation analysis for EB-1A/O-1 visa applications.

A toolkit for transforming academic publication records into evidence for
immigration petitions through field-normalized citation analysis.
"""

from .analysis import (
    DataMerger,
    FieldNormalizer,
    IndependenceClassifier,
    UptakeAggregator,
)
from .core.models import Author, Citation, Institution, PaperRecord
from .data_acquisition import OpenAlexClient, iCiteClient
from .visualization import (
    ChartGenerator,
    CitationMapFactory,
    LawyerReportGenerator,
    StreamlitDashboard,
)

__version__ = "0.3.0"  # Phase 3 - Visualization & Reporting

__all__ = [
    # Core models
    "PaperRecord",
    "Author",
    "Institution",
    "Citation",
    # Data acquisition
    "OpenAlexClient",
    "iCiteClient",
    # Analysis modules
    "DataMerger",
    "FieldNormalizer",
    "IndependenceClassifier",
    "UptakeAggregator",
    # Visualization & reporting
    "CitationMapFactory",
    "ChartGenerator",
    "StreamlitDashboard",
    "LawyerReportGenerator",
]
