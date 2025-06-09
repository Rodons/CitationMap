"""Visualization and reporting modules for CitationMap."""

try:
    from .maps import CitationMapFactory
except ImportError:
    CitationMapFactory = None

try:
    from .charts import ChartGenerator
except ImportError:
    ChartGenerator = None

# Temporarily comment out dashboard import due to import issues
# try:
#     from .dashboards import StreamlitDashboard
# except ImportError:
StreamlitDashboard = None

try:
    from .reports import LawyerReportGenerator
except ImportError:
    LawyerReportGenerator = None

__all__ = [
    "CitationMapFactory",
    "ChartGenerator",
    "StreamlitDashboard",
    "LawyerReportGenerator",
]
