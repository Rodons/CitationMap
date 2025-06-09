"""Tests for visualization modules."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from src.citationmap.core.models import Author, FieldOfStudy, Institution, PaperRecord
from src.citationmap.visualization.charts import ChartGenerator
from src.citationmap.visualization.maps import CitationMapFactory
from src.citationmap.visualization.reports import LawyerReportGenerator


@pytest.fixture
def sample_papers():
    """Create sample papers for testing."""
    author1 = Author(
        id="author1",
        display_name="Dr. Jane Smith",
        orcid="0000-0000-0000-0001",
        institutions=[
            Institution(
                id="inst1",
                display_name="MIT",
                country_code="US",
                latitude=42.3601,
                longitude=-71.0942,
            )
        ],
    )

    return [
        PaperRecord(
            id="paper1",
            title="Machine Learning Applications in Drug Discovery",
            doi="10.1000/test1",
            year=2020,
            journal="Nature",
            citation_count=150,
            rcr=3.5,
            primary_field="Computer Science",
            authors=[author1],
            fields_of_study=[
                FieldOfStudy(
                    id="field1", display_name="Computer Science", level=0, score=0.9
                )
            ],
        ),
        PaperRecord(
            id="paper2",
            title="Deep Learning for Medical Imaging",
            doi="10.1000/test2",
            year=2019,
            journal="Science",
            citation_count=95,
            rcr=2.8,
            primary_field="Medicine",
            authors=[author1],
        ),
    ]


class TestChartGenerator:
    """Test ChartGenerator functionality."""

    def test_initialization(self):
        """Test chart generator initialization."""
        generator = ChartGenerator()
        assert hasattr(generator, "merger")
        assert hasattr(generator, "aggregator")

    def test_create_rcr_distribution_chart(self, sample_papers):
        """Test RCR distribution chart creation."""
        generator = ChartGenerator()

        fig = generator.create_rcr_distribution_chart(sample_papers)

        assert fig is not None
        assert hasattr(fig, "data")

    def test_export_chart(self, sample_papers):
        """Test chart export functionality."""
        generator = ChartGenerator()

        fig = generator.create_rcr_distribution_chart(sample_papers)

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result_path = generator.export_chart(fig, tmp_path, "html")
            assert result_path == tmp_path
            assert Path(tmp_path).exists()
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestCitationMapFactory:
    """Test CitationMapFactory functionality."""

    def test_initialization(self):
        """Test map factory initialization."""
        factory = CitationMapFactory()
        assert hasattr(factory, "merger")


class TestLawyerReportGenerator:
    """Test LawyerReportGenerator functionality."""

    def test_initialization(self):
        """Test report generator initialization."""
        generator = LawyerReportGenerator()
        assert hasattr(generator, "merger")
        assert hasattr(generator, "normalizer")
        assert hasattr(generator, "classifier")
        assert hasattr(generator, "aggregator")
