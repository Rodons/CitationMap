"""Data acquisition modules for external APIs."""

from .openalex import OpenAlexClient
from .icite import iCiteClient
from .cache import CacheManager

__all__ = ["OpenAlexClient", "iCiteClient", "CacheManager"] 