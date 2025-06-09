"""Interactive charts using Plotly."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from ..analysis import DataMerger, UptakeAggregator
from ..core.models import PaperRecord

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates interactive charts for citation analysis."""

    def __init__(self):
        """Initialize chart generator."""
        self.logger = logger
        self.merger = DataMerger()
        self.aggregator = UptakeAggregator()
        pio.templates.default = "plotly_white"

    def create_citation_timeline(
        self, papers: List[PaperRecord], title: str = "Citation Timeline"
    ) -> go.Figure:
        """Create timeline chart showing citations over time."""
        papers_df = self.merger.papers_to_dataframe(papers)

        if papers_df.empty:
            return self._create_empty_chart("No data available")

        yearly_data = (
            papers_df.groupby("year")
            .agg({"citation_count": ["sum", "count"], "independent_citations": "sum"})
            .reset_index()
        )

        yearly_data.columns = [
            "year",
            "total_citations",
            "paper_count",
            "independent_citations",
        ]

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Bar(
                x=yearly_data["year"],
                y=yearly_data["total_citations"],
                name="Total Citations",
                marker_color="lightblue",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=yearly_data["year"],
                y=yearly_data["paper_count"],
                mode="lines+markers",
                name="Papers Published",
                line=dict(color="red", width=3),
            ),
            secondary_y=True,
        )

        fig.update_xaxes(title_text="Year")
        fig.update_yaxes(title_text="Citations", secondary_y=False)
        fig.update_yaxes(title_text="Papers", secondary_y=True)
        fig.update_layout(title=title, height=500)

        return fig

    def create_field_comparison_chart(
        self, papers: List[PaperRecord], title: str = "Citation Impact by Field"
    ) -> go.Figure:
        """Create chart comparing impact across fields."""
        papers_df = self.merger.papers_to_dataframe(papers)
        field_metrics = self.merger.aggregate_field_metrics(papers_df)

        if field_metrics.empty:
            return self._create_empty_chart("No field data available")

        fig = px.bar(
            field_metrics,
            x="field_name",
            y="total_citations",
            title=title,
            labels={"field_name": "Field", "total_citations": "Total Citations"},
        )

        return fig

    def create_rcr_distribution_chart(
        self, papers: List[PaperRecord], title: str = "RCR Distribution"
    ) -> go.Figure:
        """Create histogram of RCR values."""
        rcr_values = [p.rcr for p in papers if p.rcr is not None and p.rcr > 0]

        if not rcr_values:
            return self._create_empty_chart("No RCR data available")

        fig = go.Figure(data=[go.Histogram(x=rcr_values, nbinsx=20)])
        fig.add_vline(x=1.0, line_dash="dash", line_color="green")
        fig.add_vline(x=2.0, line_dash="dash", line_color="orange")
        fig.update_layout(
            title=title,
            xaxis_title="Relative Citation Ratio (RCR)",
            yaxis_title="Number of Papers",
        )

        return fig

    def export_chart(
        self, fig: go.Figure, filename: str, format_type: str = "html"
    ) -> str:
        """Export chart to file."""
        if format_type.lower() == "html":
            fig.write_html(filename)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        self.logger.info(f"Chart exported to {filename}")
        return filename

    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        fig.update_layout(
            xaxis=dict(visible=False), yaxis=dict(visible=False), height=400
        )
        return fig
