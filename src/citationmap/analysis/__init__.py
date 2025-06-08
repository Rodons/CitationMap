"""Core analysis modules for citation data processing."""

from .merger import DataMerger
from .field_norm import FieldNormalizer
from .independence import IndependenceClassifier
from .uptake import UptakeAggregator

__all__ = [
    "DataMerger",
    "FieldNormalizer", 
    "IndependenceClassifier",
    "UptakeAggregator"
] 