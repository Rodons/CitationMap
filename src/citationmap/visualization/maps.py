"""Interactive citation maps using Folium."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import folium
import pandas as pd
from folium import plugins

from ..analysis import DataMerger
from ..core.models import Institution, PaperRecord

logger = logging.getLogger(__name__)


class CitationMapFactory:
    """Creates interactive citation maps for geographic analysis."""

    def __init__(self):
        """Initialize map factory."""
        self.logger = logger
        self.merger = DataMerger()

    def create_global_citation_map(
        self,
        papers: List[PaperRecord],
        center_lat: float = 20.0,
        center_lon: float = 0.0,
        zoom_start: int = 2,
    ) -> folium.Map:
        """Create a global map showing citation sources by country.

        Args:
            papers: List of paper records
            center_lat: Map center latitude
            center_lon: Map center longitude
            zoom_start: Initial zoom level

        Returns:
            Folium map object
        """
        # Create base map
        citation_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles="OpenStreetMap",
        )

        # Get institution data
        institutions_df = self.merger.create_institutions_dataframe(papers)

        if institutions_df.empty:
            self.logger.warning("No institution data available for mapping")
            return citation_map

        # Aggregate by country
        country_data = self._aggregate_country_data(institutions_df)

        # Add country markers
        for country_info in country_data:
            if country_info["lat"] and country_info["lon"]:
                self._add_country_marker(citation_map, country_info)

        # Add legend
        self._add_citation_legend(citation_map)

        # Add fullscreen button
        plugins.Fullscreen().add_to(citation_map)

        return citation_map

    def export_map_html(
        self, map_obj: folium.Map, filename: str, title: str = "Citation Map"
    ) -> str:
        """Export map to HTML file with custom styling."""
        # Save map to file
        map_obj.save(filename)
        self.logger.info(f"Map exported to {filename}")
        return filename

    def _aggregate_country_data(
        self, institutions_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Aggregate institution data by country."""
        country_aggregation = (
            institutions_df.groupby("institution_country")
            .agg(
                {
                    "paper_id": "count",
                    "author_name": lambda x: len(set(x)),
                    "institution_name": lambda x: len(set(x)),
                }
            )
            .reset_index()
        )

        # Add country coordinates (simplified)
        country_coords = {
            "US": (39.8283, -98.5795),
            "GB": (55.3781, -3.4360),
            "DE": (51.1657, 10.4515),
            "FR": (46.6034, 1.8883),
            "CA": (56.1304, -106.3468),
            "AU": (-25.2744, 133.7751),
            "JP": (36.2048, 138.2529),
            "CN": (35.8617, 104.1954),
            "IN": (20.5937, 78.9629),
            "BR": (-14.2350, -51.9253),
        }

        country_data = []
        for _, row in country_aggregation.iterrows():
            country_code = row["institution_country"]
            coords = country_coords.get(country_code, (None, None))

            country_data.append(
                {
                    "country": country_code,
                    "lat": coords[0],
                    "lon": coords[1],
                    "papers": row["paper_id"],
                    "authors": row["author_name"],
                    "institutions": row["institution_name"],
                }
            )

        return country_data

    def _add_country_marker(self, map_obj: folium.Map, country_info: Dict[str, Any]):
        """Add country marker to map."""
        # Calculate marker size based on paper count
        base_size = 10
        size = base_size + (country_info["papers"] * 2)
        size = min(size, 50)  # Cap maximum size

        # Color based on paper count
        if country_info["papers"] >= 10:
            color = "red"
        elif country_info["papers"] >= 5:
            color = "orange"
        else:
            color = "blue"

        # Create popup text
        popup_text = f"""
        <b>{country_info['country']}</b><br>
        Papers: {country_info['papers']}<br>
        Authors: {country_info['authors']}<br>
        Institutions: {country_info['institutions']}
        """

        folium.CircleMarker(
            location=[country_info["lat"], country_info["lon"]],
            radius=size,
            popup=popup_text,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
        ).add_to(map_obj)

    def _add_citation_legend(self, map_obj: folium.Map):
        """Add legend to citation map."""
        legend_html = """
        <div style="position: fixed;
                    bottom: 50px; left: 50px; width: 200px; height: 90px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    font-size:14px; padding: 10px">
        <p><b>Citation Sources</b></p>
        <p><i class="fa fa-circle" style="color:red"></i> 10+ papers</p>
        <p><i class="fa fa-circle" style="color:orange"></i> 5-9 papers</p>
        <p><i class="fa fa-circle" style="color:blue"></i> 1-4 papers</p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))
