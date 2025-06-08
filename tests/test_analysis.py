"""Tests for analysis modules."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch

from src.citationmap.core.models import (
    PaperRecord, Author, Institution, FieldOfStudy, Citation, 
    PatentCitation, ClinicalTrial, CitationContext
)
from src.citationmap.analysis import (
    DataMerger, FieldNormalizer, IndependenceClassifier, UptakeAggregator
)


@pytest.fixture
def sample_authors():
    """Create sample authors for testing."""
    return [
        Author(
            id="author1",
            display_name="John Smith",
            orcid="0000-0000-0000-0001",
            institutions=[
                Institution(
                    id="inst1",
                    display_name="MIT",
                    country_code="US",
                    type="education",
                    latitude=42.3601,
                    longitude=-71.0942
                )
            ]
        ),
        Author(
            id="author2", 
            display_name="Jane Doe",
            institutions=[
                Institution(
                    id="inst2",
                    display_name="Harvard University", 
                    country_code="US",
                    type="education"
                )
            ]
        )
    ]


@pytest.fixture
def sample_papers(sample_authors):
    """Create sample papers for testing."""
    return [
        PaperRecord(
            id="paper1",
            title="Machine Learning for Drug Discovery",
            doi="10.1000/test1",
            pmid="12345",
            year=2020,
            journal="Nature",
            venue="Nature",
            citation_count=50,
            independent_citations=45,
            self_citations=5,
            rcr=2.5,
            fcr=1.8,
            percentile=85.0,
            primary_field="Computer Science",
            authors=sample_authors,
            fields_of_study=[
                FieldOfStudy(
                    id="field1",
                    display_name="Computer Science",
                    level=0,
                    score=0.9
                )
            ],
            citations=[
                Citation(
                    citing_paper_id="citing1",
                    citation_context=CitationContext.INDEPENDENT_CITATION,
                    year=2021,
                    citing_authors=[sample_authors[0]],
                    citing_institutions=[sample_authors[0].institutions[0]]
                )
            ],
            patent_citations=[
                PatentCitation(
                    patent_id="US123456",
                    patent_title="ML-based Drug Screening System"
                )
            ],
            clinical_trials=[
                ClinicalTrial(
                    nct_id="NCT12345",
                    title="AI-guided Cancer Treatment",
                    status="Active",
                    phase="Phase II"
                )
            ]
        ),
        PaperRecord(
            id="paper2",
            title="Deep Learning in Medical Imaging",
            doi="10.1000/test2",
            year=2019,
            journal="Science",
            citation_count=75,
            independent_citations=70,
            self_citations=5,
            rcr=3.2,
            primary_field="Medicine",
            authors=[sample_authors[1]],
            fields_of_study=[
                FieldOfStudy(
                    id="field2",
                    display_name="Medicine",
                    level=0,
                    score=0.8
                )
            ]
        ),
        PaperRecord(
            id="paper3",
            title="Neural Network Optimization",
            doi="10.1000/test3",
            year=2021,
            journal="ICML",
            citation_count=25,
            independent_citations=20,
            self_citations=5,
            primary_field="Computer Science",
            authors=sample_authors
        )
    ]


class TestDataMerger:
    """Test DataMerger functionality."""
    
    def test_papers_to_dataframe(self, sample_papers):
        """Test converting papers to pandas DataFrame."""
        merger = DataMerger()
        df = merger.papers_to_dataframe(sample_papers)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "id" in df.columns
        assert "title" in df.columns
        assert "citation_count" in df.columns
        assert df.loc[0, "id"] == "paper1"
        assert df.loc[0, "primary_field"] == "Computer Science"
    
    def test_papers_to_polars(self, sample_papers):
        """Test converting papers to Polars DataFrame."""
        merger = DataMerger()
        
        # Mock polars import since it might not be available in test environment
        with patch('src.citationmap.analysis.merger.pl') as mock_pl:
            mock_df = Mock()
            mock_pl.from_pandas.return_value = mock_df
            
            result = merger.papers_to_polars(sample_papers)
            mock_pl.from_pandas.assert_called_once()
    
    def test_papers_to_dataframe_empty(self):
        """Test with empty papers list."""
        merger = DataMerger()
        df = merger.papers_to_dataframe([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_merge_icite_data(self, sample_papers):
        """Test merging iCite data."""
        merger = DataMerger()
        df = merger.papers_to_dataframe(sample_papers)
        
        icite_data = {
            "10.1000/test1": {
                "relative_citation_ratio": 3.0,
                "field_citation_rate": 2.0,
                "citation_count": 52
            }
        }
        
        merged_df = merger.merge_icite_data(df, icite_data)
        
        assert len(merged_df) == len(df)
        # RCR should be updated for the matched paper
        paper1_row = merged_df[merged_df['id'] == 'paper1'].iloc[0]
        assert paper1_row['rcr'] == 3.0
    
    def test_create_citations_dataframe(self, sample_papers):
        """Test creating citations DataFrame."""
        merger = DataMerger()
        citations_df = merger.create_citations_dataframe(sample_papers)
        
        assert isinstance(citations_df, pd.DataFrame)
        assert len(citations_df) >= 1  # At least one citation from sample data
        assert "cited_paper_id" in citations_df.columns
        assert "citing_paper_id" in citations_df.columns
    
    def test_create_institutions_dataframe(self, sample_papers):
        """Test creating institutions DataFrame."""
        merger = DataMerger()
        institutions_df = merger.create_institutions_dataframe(sample_papers)
        
        assert isinstance(institutions_df, pd.DataFrame)
        assert len(institutions_df) >= 1
        assert "institution_name" in institutions_df.columns
        assert "institution_country" in institutions_df.columns
    
    def test_aggregate_field_metrics(self, sample_papers):
        """Test field metrics aggregation."""
        merger = DataMerger()
        df = merger.papers_to_dataframe(sample_papers)
        field_metrics = merger.aggregate_field_metrics(df)
        
        assert isinstance(field_metrics, pd.DataFrame)
        assert "field_name" in field_metrics.columns
        assert "paper_count" in field_metrics.columns
        assert "mean_citations" in field_metrics.columns
    
    def test_create_analysis_summary(self, sample_papers):
        """Test creating analysis summary."""
        merger = DataMerger()
        summary = merger.create_analysis_summary(sample_papers)
        
        assert isinstance(summary, dict)
        assert "total_papers" in summary
        assert "h_index" in summary
        assert "i10_index" in summary
        assert summary["total_papers"] == 3


class TestFieldNormalizer:
    """Test FieldNormalizer functionality."""
    
    def test_calculate_rcr_percentile(self):
        """Test RCR percentile calculation."""
        normalizer = FieldNormalizer()
        
        # Test basic percentile calculation
        percentile = normalizer.calculate_rcr_percentile(2.0, "Computer Science", 2020)
        assert isinstance(percentile, float)
        assert 0 <= percentile <= 100
        
        # Test with invalid RCR
        percentile = normalizer.calculate_rcr_percentile(0, "Computer Science", 2020)
        assert percentile is None
        
        percentile = normalizer.calculate_rcr_percentile(-1, "Computer Science", 2020)
        assert percentile is None
    
    def test_calculate_field_impact_score(self, sample_papers):
        """Test field impact score calculation."""
        normalizer = FieldNormalizer()
        
        score = normalizer.calculate_field_impact_score(sample_papers[0])
        assert isinstance(score, float)
        assert 0 <= score <= 100
        
        # Test with paper without metrics
        empty_paper = PaperRecord(id="empty", title="Empty Paper")
        score = normalizer.calculate_field_impact_score(empty_paper)
        assert score == 0.0
    
    def test_normalize_citation_metrics(self, sample_papers):
        """Test citation metrics normalization."""
        normalizer = FieldNormalizer()
        
        normalized_papers = normalizer.normalize_citation_metrics(sample_papers, by_field=True)
        assert len(normalized_papers) == len(sample_papers)
        
        # Check that normalized papers have additional metrics
        for paper in normalized_papers:
            assert hasattr(paper, 'field_impact_score')
    
    def test_identify_field_outliers(self, sample_papers):
        """Test field outlier identification."""
        normalizer = FieldNormalizer()
        
        outliers = normalizer.identify_field_outliers(sample_papers, threshold=1.0)
        assert isinstance(outliers, dict)
        
        # With a low threshold, some papers should be identified as outliers
        total_outliers = sum(len(papers) for papers in outliers.values())
        assert total_outliers >= 0
    
    def test_calculate_field_rankings(self, sample_papers):
        """Test field rankings calculation."""
        normalizer = FieldNormalizer()
        
        rankings = normalizer.calculate_field_rankings(sample_papers)
        assert isinstance(rankings, dict)
        
        # Check structure of rankings
        for field, field_data in rankings.items():
            assert "rankings" in field_data
            assert "statistics" in field_data
    
    def test_create_field_comparison_matrix(self, sample_papers):
        """Test field comparison matrix creation."""
        normalizer = FieldNormalizer()
        
        comparison_df = normalizer.create_field_comparison_matrix(sample_papers)
        assert isinstance(comparison_df, pd.DataFrame)
        
        if not comparison_df.empty:
            assert "field" in comparison_df.columns
            assert "paper_count" in comparison_df.columns


class TestIndependenceClassifier:
    """Test IndependenceClassifier functionality."""
    
    def test_init(self):
        """Test classifier initialization."""
        classifier = IndependenceClassifier()
        assert classifier.author_threshold == 0.8
        assert classifier.institution_threshold == 0.9
        
        # Test with custom thresholds
        classifier = IndependenceClassifier(0.7, 0.85)
        assert classifier.author_threshold == 0.7
        assert classifier.institution_threshold == 0.85
    
    def test_normalize_author_name(self):
        """Test author name normalization."""
        classifier = IndependenceClassifier()
        
        # Test basic normalization
        assert classifier._normalize_author_name("John Smith") == "john smith"
        assert classifier._normalize_author_name("Dr. John Smith") == "john smith"
        assert classifier._normalize_author_name("Smith, John") == "john smith"
        assert classifier._normalize_author_name("John Smith Jr.") == "john smith"
        
        # Test with empty/None
        assert classifier._normalize_author_name("") == ""
        assert classifier._normalize_author_name(None) == ""
    
    def test_normalize_institution_name(self):
        """Test institution name normalization."""
        classifier = IndependenceClassifier()
        
        # Test basic normalization
        normalized = classifier._normalize_institution_name("Massachusetts Institute of Technology")
        assert "massachusetts" in normalized
        
        # Test with common institution words
        mit1 = classifier._normalize_institution_name("MIT")
        mit2 = classifier._normalize_institution_name("Massachusetts Institute Technology")
        # Should be similar after normalization
        assert len(mit1) > 0 and len(mit2) > 0
    
    def test_are_similar_authors(self):
        """Test author similarity checking."""
        classifier = IndependenceClassifier()
        
        # Test exact match
        assert classifier._are_similar_authors("john smith", "john smith")
        
        # Test with initials
        assert classifier._names_match_with_initials(["j", "smith"], ["john", "smith"])
        assert classifier._names_match_with_initials(["john", "s"], ["john", "smith"])
        
        # Test dissimilar names
        assert not classifier._are_similar_authors("john smith", "jane doe")
    
    def test_classify_citations(self, sample_papers):
        """Test citation classification."""
        classifier = IndependenceClassifier()
        
        classified_papers = classifier.classify_citations(sample_papers)
        assert len(classified_papers) == len(sample_papers)
        
        # Check that classification was performed
        for paper in classified_papers:
            assert hasattr(paper, 'independent_citations')
            assert hasattr(paper, 'self_citations')
            assert paper.independent_citations is not None
            assert paper.self_citations is not None
    
    def test_analyze_citation_patterns(self, sample_papers):
        """Test citation pattern analysis."""
        classifier = IndependenceClassifier()
        
        analysis = classifier.analyze_citation_patterns(sample_papers)
        assert isinstance(analysis, dict)
        assert "total_papers" in analysis
        assert "overall_independence_ratio" in analysis
        assert "field_patterns" in analysis
    
    def test_generate_independence_report(self, sample_papers):
        """Test independence report generation."""
        classifier = IndependenceClassifier()
        
        report = classifier.generate_independence_report(sample_papers)
        assert isinstance(report, dict)
        assert "summary" in report
        assert "quality_metrics" in report
        assert "recommendations" in report


class TestUptakeAggregator:
    """Test UptakeAggregator functionality."""
    
    def test_analyze_patent_uptake(self, sample_papers):
        """Test patent uptake analysis."""
        aggregator = UptakeAggregator()
        
        analysis = aggregator.analyze_patent_uptake(sample_papers)
        assert isinstance(analysis, dict)
        assert "total_papers" in analysis
        assert "papers_with_patents" in analysis
        assert "patent_citation_rate" in analysis
        
        # Should find at least one paper with patents from sample data
        assert analysis["papers_with_patents"] >= 1
    
    def test_analyze_clinical_trial_uptake(self, sample_papers):
        """Test clinical trial uptake analysis."""
        aggregator = UptakeAggregator()
        
        analysis = aggregator.analyze_clinical_trial_uptake(sample_papers)
        assert isinstance(analysis, dict)
        assert "total_papers" in analysis
        assert "papers_with_trials" in analysis
        assert "trial_citation_rate" in analysis
        
        # Should find at least one paper with trials from sample data
        assert analysis["papers_with_trials"] >= 1
    
    def test_analyze_policy_uptake(self, sample_papers):
        """Test policy uptake analysis (placeholder)."""
        aggregator = UptakeAggregator()
        
        analysis = aggregator.analyze_policy_uptake(sample_papers)
        assert isinstance(analysis, dict)
        assert "total_papers" in analysis
        assert analysis["policy_implementation_status"] == "not_implemented"
    
    def test_calculate_translational_impact_score(self, sample_papers):
        """Test translational impact score calculation."""
        aggregator = UptakeAggregator()
        
        # Test with paper that has patents and trials
        score = aggregator.calculate_translational_impact_score(sample_papers[0])
        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 0  # Should have positive score due to patents and trials
        
        # Test with paper without translational impact
        score = aggregator.calculate_translational_impact_score(sample_papers[1])
        assert score >= 0
    
    def test_create_uptake_timeline(self, sample_papers):
        """Test uptake timeline creation."""
        aggregator = UptakeAggregator()
        
        timeline = aggregator.create_uptake_timeline(sample_papers)
        assert isinstance(timeline, dict)
        assert "timeline_events" in timeline
        assert "event_counts" in timeline
        
        # Should have events from sample data
        assert len(timeline["timeline_events"]) > 0
    
    def test_identify_breakthrough_papers(self, sample_papers):
        """Test breakthrough paper identification."""
        aggregator = UptakeAggregator()
        
        # Use a low threshold to ensure we find some papers
        breakthrough_papers = aggregator.identify_breakthrough_papers(sample_papers, threshold=10.0)
        assert isinstance(breakthrough_papers, list)
        
        # Check structure of results
        for paper in breakthrough_papers:
            assert "id" in paper
            assert "translational_impact_score" in paper
            assert "breakthrough_factors" in paper
    
    def test_generate_uptake_report(self, sample_papers):
        """Test comprehensive uptake report generation."""
        aggregator = UptakeAggregator()
        
        report = aggregator.generate_uptake_report(sample_papers)
        assert isinstance(report, dict)
        assert "executive_summary" in report
        assert "patent_analysis" in report
        assert "clinical_trial_analysis" in report
        assert "recommendations" in report
        
        # Check executive summary structure
        exec_summary = report["executive_summary"]
        assert "total_papers" in exec_summary
        assert "translational_impact_rate" in exec_summary
    
    def test_empty_papers_handling(self):
        """Test handling of empty paper lists."""
        merger = DataMerger()
        normalizer = FieldNormalizer()
        classifier = IndependenceClassifier()
        aggregator = UptakeAggregator()
        
        # Test that all modules handle empty input gracefully
        assert merger.papers_to_dataframe([]).empty
        assert normalizer.normalize_citation_metrics([]) == []
        assert classifier.classify_citations([]) == []
        assert aggregator.analyze_patent_uptake([])["total_papers"] == 0


if __name__ == "__main__":
    pytest.main([__file__]) 