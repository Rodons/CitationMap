"""Tests for CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from src.citationmap.cli.main import app
from src.citationmap.core.models import Author, Institution, PaperRecord


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_papers():
    """Create sample papers for testing."""
    author = Author(
        id="author1",
        display_name="Dr. Test Author",
        orcid="0000-0000-0000-0001",
        institutions=[
            Institution(
                id="inst1",
                display_name="Test University",
                country_code="US",
                type="education",
            )
        ],
    )

    return [
        PaperRecord(
            id="paper1",
            title="Test Paper 1",
            doi="10.1000/test1",
            year=2020,
            journal="Nature",
            citation_count=50,
            rcr=2.5,
            authors=[author],
        ),
        PaperRecord(
            id="paper2",
            title="Test Paper 2",
            doi="10.1000/test2",
            year=2021,
            journal="Science",
            citation_count=30,
            rcr=1.8,
            authors=[author],
        ),
    ]


class TestCLICommands:
    """Test CLI command functionality."""

    @patch("src.citationmap.cli.main._fetch_papers")
    @patch("src.citationmap.cli.main._run_analysis")
    @patch("src.citationmap.cli.main._generate_reports")
    @patch("src.citationmap.cli.main._display_summary")
    def test_analyze_command_success(
        self,
        mock_display,
        mock_reports,
        mock_analysis,
        mock_fetch,
        runner,
        sample_papers,
    ):
        """Test successful analyze command execution."""
        # Mock the functions
        mock_fetch.return_value = sample_papers
        mock_analysis.return_value = {
            "summary": {
                "total_papers": 2,
                "total_citations": 80,
                "h_index": 2,
                "i10_index": 1,
                "independence_ratio": 0.9,
            },
            "independence": {"quality_metrics": {}},
            "uptake": {"executive_summary": {}},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                app,
                [
                    "analyze",
                    "0000-0000-0000-0001",
                    "--output",
                    temp_dir,
                    "--name",
                    "Dr. Test Author",
                ],
            )

        assert result.exit_code == 0
        mock_fetch.assert_called_once_with("0000-0000-0000-0001")
        mock_analysis.assert_called_once()
        mock_reports.assert_called_once()
        mock_display.assert_called_once()

    @patch("src.citationmap.cli.main._fetch_papers")
    def test_analyze_command_no_papers(self, mock_fetch, runner):
        """Test analyze command when no papers are found."""
        mock_fetch.return_value = []

        result = runner.invoke(app, ["analyze", "0000-0000-0000-0001"])

        assert result.exit_code == 1
        assert "No papers found" in result.stdout

    @patch("src.citationmap.cli.main._fetch_papers")
    @patch("src.citationmap.cli.main._run_analysis")
    @patch("src.citationmap.cli.main._display_summary")
    def test_stats_command_success(
        self, mock_display, mock_analysis, mock_fetch, runner, sample_papers
    ):
        """Test successful stats command execution."""
        mock_fetch.return_value = sample_papers
        mock_analysis.return_value = {
            "summary": {
                "total_papers": 2,
                "total_citations": 80,
                "h_index": 2,
                "i10_index": 1,
                "independence_ratio": 0.9,
            }
        }

        result = runner.invoke(app, ["stats", "0000-0000-0000-0001"])

        assert result.exit_code == 0
        mock_fetch.assert_called_once_with("0000-0000-0000-0001")
        mock_analysis.assert_called_once()
        mock_display.assert_called_once()

    @patch("src.citationmap.cli.main._fetch_papers")
    def test_stats_command_no_papers(self, mock_fetch, runner):
        """Test stats command when no papers are found."""
        mock_fetch.return_value = []

        result = runner.invoke(app, ["stats", "0000-0000-0000-0001"])

        assert result.exit_code == 1
        assert "No papers found" in result.stdout


class TestCLIHelperFunctions:
    """Test CLI helper functions."""

    @patch("src.citationmap.cli.main.OpenAlexClient")
    @patch("src.citationmap.cli.main.iCiteClient")
    def test_fetch_papers(self, mock_icite_client, mock_openalex_client, sample_papers):
        """Test paper fetching functionality."""
        from src.citationmap.cli.main import _fetch_papers

        # Mock OpenAlex client
        mock_openalex = Mock()
        mock_openalex.fetch_papers_by_orcid.return_value = sample_papers
        mock_openalex_client.return_value = mock_openalex

        # Mock iCite client
        mock_icite = Mock()
        mock_icite.fetch_paper_metrics.return_value = {"relative_citation_ratio": 3.0}
        mock_icite_client.return_value = mock_icite

        result = _fetch_papers("0000-0000-0000-0001")

        assert len(result) == 2
        assert result[0].title == "Test Paper 1"
        mock_openalex.fetch_papers_by_orcid.assert_called_once_with(
            "0000-0000-0000-0001"
        )

    @patch("src.citationmap.cli.main.DataMerger")
    @patch("src.citationmap.cli.main.IndependenceClassifier")
    @patch("src.citationmap.cli.main.UptakeAggregator")
    def test_run_analysis(
        self,
        mock_aggregator_class,
        mock_classifier_class,
        mock_merger_class,
        sample_papers,
    ):
        """Test analysis execution functionality."""
        from src.citationmap.cli.main import _run_analysis

        # Mock components
        mock_merger = Mock()
        mock_merger.create_analysis_summary.return_value = {
            "total_papers": 2,
            "total_citations": 80,
            "h_index": 2,
        }
        mock_merger_class.return_value = mock_merger

        mock_classifier = Mock()
        mock_classifier.generate_independence_report.return_value = {
            "quality_metrics": {"independence_quality_score": 85.0}
        }
        mock_classifier_class.return_value = mock_classifier

        mock_aggregator = Mock()
        mock_aggregator.generate_uptake_report.return_value = {
            "executive_summary": {"translational_impact_rate": 0.5}
        }
        mock_aggregator_class.return_value = mock_aggregator

        result = _run_analysis(sample_papers)

        assert "summary" in result
        assert "independence" in result
        assert "uptake" in result
        assert result["summary"]["total_papers"] == 2

    @patch("src.citationmap.cli.main.LawyerReportGenerator")
    @patch("src.citationmap.cli.main.ChartGenerator")
    def test_generate_reports(
        self, mock_chart_generator_class, mock_report_generator_class, sample_papers
    ):
        """Test report generation functionality."""
        from src.citationmap.cli.main import _generate_reports

        # Mock report generator
        mock_report_generator = Mock()
        mock_report_generator.generate_one_page_exhibit.return_value = "exhibit.html"
        mock_report_generator.generate_summary_report.return_value = "summary.txt"
        mock_report_generator_class.return_value = mock_report_generator

        # Mock chart generator
        mock_chart_generator = Mock()
        mock_timeline_fig = Mock()
        mock_field_fig = Mock()
        mock_chart_generator.create_citation_timeline.return_value = mock_timeline_fig
        mock_chart_generator.create_field_comparison_chart.return_value = mock_field_fig
        mock_chart_generator.export_chart.return_value = "chart.html"
        mock_chart_generator_class.return_value = mock_chart_generator

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            _generate_reports(sample_papers, output_path, "Test Author")

        # Verify reports were generated
        mock_report_generator.generate_one_page_exhibit.assert_called_once()
        mock_report_generator.generate_summary_report.assert_called_once()
        mock_chart_generator.create_citation_timeline.assert_called_once()
        mock_chart_generator.create_field_comparison_chart.assert_called_once()

    def test_display_summary(self, sample_papers):
        """Test summary display functionality."""
        from src.citationmap.cli.main import _display_summary

        analysis_results = {
            "summary": {
                "total_papers": 2,
                "total_citations": 80,
                "h_index": 2,
                "i10_index": 1,
                "independence_ratio": 0.9,
            }
        }

        # This should not raise any exceptions
        _display_summary(sample_papers, analysis_results)


class TestCLIErrorHandling:
    """Test CLI error handling."""

    @patch("src.citationmap.cli.main._fetch_papers")
    def test_analyze_command_exception(self, mock_fetch, runner):
        """Test analyze command handles exceptions gracefully."""
        mock_fetch.side_effect = Exception("API Error")

        result = runner.invoke(app, ["analyze", "0000-0000-0000-0001"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    @patch("src.citationmap.cli.main._fetch_papers")
    def test_stats_command_exception(self, mock_fetch, runner):
        """Test stats command handles exceptions gracefully."""
        mock_fetch.side_effect = Exception("API Error")

        result = runner.invoke(app, ["stats", "0000-0000-0000-0001"])

        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    def test_help_command(self, runner):
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "CitationMap" in result.stdout
        assert "analyze" in result.stdout
        assert "stats" in result.stdout

    def test_analyze_help(self, runner):
        """Test analyze command help."""
        result = runner.invoke(app, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "ORCID ID" in result.stdout

    def test_stats_help(self, runner):
        """Test stats command help."""
        result = runner.invoke(app, ["stats", "--help"])

        assert result.exit_code == 0
        assert "ORCID ID" in result.stdout
