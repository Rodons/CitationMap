"""Tests for core data models."""

import pytest
from datetime import datetime
from citationmap.core.models import (
    Author,
    Institution,
    PaperRecord,
    FieldOfStudy,
    AnalysisResult,
    CitationContext,
)


class TestInstitution:
    """Test Institution model."""

    def test_institution_creation(self):
        """Test basic institution creation."""
        institution = Institution(display_name="MIT")
        assert institution.display_name == "MIT"
        assert institution.id is None
        assert institution.country_code is None

    def test_institution_with_location(self):
        """Test institution with geographic data."""
        institution = Institution(
            display_name="MIT",
            country_code="US",
            latitude=42.3601,
            longitude=-71.0942,
        )
        assert institution.country_code == "US"
        assert institution.latitude == 42.3601
        assert institution.longitude == -71.0942


class TestAuthor:
    """Test Author model."""

    def test_author_creation(self):
        """Test basic author creation."""
        author = Author(display_name="John Doe")
        assert author.display_name == "John Doe"
        assert author.orcid is None
        assert len(author.institutions) == 0
        assert author.is_corresponding is False


class TestFieldOfStudy:
    """Test FieldOfStudy model."""

    def test_field_creation(self):
        """Test field of study creation."""
        field = FieldOfStudy(
            id="cs", display_name="Computer Science", level=1, score=0.95
        )
        assert field.display_name == "Computer Science"
        assert field.score == 0.95

    def test_field_score_validation(self):
        """Test that score is validated to be between 0 and 1."""
        with pytest.raises(ValueError):
            FieldOfStudy(id="cs", display_name="CS", level=1, score=1.5)


class TestPaperRecord:
    """Test PaperRecord model."""

    def test_paper_creation(self):
        """Test basic paper creation."""
        paper = PaperRecord(id="123", title="Test Paper")
        assert paper.id == "123"
        assert paper.title == "Test Paper"
        assert paper.citation_count == 0
        assert len(paper.authors) == 0

    def test_year_from_publication_date(self):
        """Test that year is extracted from publication_date."""
        pub_date = datetime(2023, 5, 15)
        paper = PaperRecord(
            id="123", title="Test Paper", publication_date=pub_date
        )
        assert paper.year == 2023


class TestAnalysisResult:
    """Test AnalysisResult model."""

    def test_analysis_result_creation(self):
        """Test basic analysis result creation."""
        result = AnalysisResult()
        assert result.total_papers == 0
        assert result.total_citations == 0
        assert len(result.papers) == 0

    def test_average_citations_per_paper(self):
        """Test average citations calculation."""
        result = AnalysisResult(total_papers=5, total_citations=50)
        assert result.average_citations_per_paper == 10.0

    def test_average_citations_zero_papers(self):
        """Test average citations with zero papers."""
        result = AnalysisResult(total_papers=0, total_citations=0)
        assert result.average_citations_per_paper == 0.0

    def test_independence_ratio(self):
        """Test independence ratio calculation."""
        result = AnalysisResult(
            total_citations=100, total_independent_citations=80
        )
        assert result.independence_ratio == 0.8

    def test_independence_ratio_zero_citations(self):
        """Test independence ratio with zero citations."""
        result = AnalysisResult(total_citations=0, total_independent_citations=0)
        assert result.independence_ratio == 0.0


class TestCitationContext:
    """Test CitationContext enum."""

    def test_citation_context_values(self):
        """Test that all citation context values are available."""
        assert CitationContext.SELF_CITATION == "self_citation"
        assert CitationContext.INSTITUTIONAL_CITATION == "institutional_citation"
        assert CitationContext.INDEPENDENT_CITATION == "independent_citation"
        assert CitationContext.UNKNOWN == "unknown" 