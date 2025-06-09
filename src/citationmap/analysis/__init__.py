"""Core analysis modules for citation data processing."""

from .field_norm import FieldNormalizer
from .independence import IndependenceClassifier
from .merger import DataMerger
from .uptake import UptakeAggregator

__all__ = [
    "DataMerger",
    "FieldNormalizer",
    "IndependenceClassifier",
    "UptakeAggregator",
]
