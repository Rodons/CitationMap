"""
CitationMap: A toolkit for transforming publication records into evidence for immigration petitions.

This package provides tools to analyze academic citations, field-normalize impact metrics,
and generate visualizations suitable for EB-1A/O-1 visa applications.
"""

__version__ = "0.1.0"
__author__ = "CitationMap Team"
__email__ = "contact@citationmap.dev"

from .core.analyzer import CitationAnalyzer
from .core.models import AnalysisResult, PaperRecord

__all__ = [
    "CitationAnalyzer", 
    "AnalysisResult", 
    "PaperRecord",
    "__version__"
] 