"""Field normalization for academic metrics."""

import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from collections import defaultdict

from ..core.models import PaperRecord

logger = logging.getLogger(__name__)


class FieldNormalizer:
    """Calculates field-normalized metrics for papers."""
    
    def __init__(self):
        """Initialize field normalizer."""
        self.logger = logger
        self.field_baselines = {}  # Cache field-specific baselines
    
    def calculate_rcr_percentile(self, rcr: float, field: str, year: int) -> Optional[float]:
        """Convert RCR to field-specific percentile.
        
        Based on iCite methodology, RCR values are log-normally distributed
        within fields. This estimates percentile position.
        
        Args:
            rcr: Relative Citation Ratio
            field: Primary field of study
            year: Publication year
            
        Returns:
            Percentile (0-100) or None if cannot calculate
        """
        if not rcr or rcr <= 0:
            return None
        
        # Empirical RCR distribution parameters by field (approximate)
        # These are rough estimates - in production, would use actual field distributions
        field_params = {
            'Medicine': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.8},
            'Biology': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.85},
            'Physics': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.75},
            'Chemistry': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.8},
            'Computer Science': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.9},
            'Engineering': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.85},
            'Mathematics': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.7},
            'Social Sciences': {'mean_log_rcr': 0.0, 'std_log_rcr': 0.9},
        }
        
        # Default parameters for unknown fields
        default_params = {'mean_log_rcr': 0.0, 'std_log_rcr': 0.8}
        
        # Get field parameters (fuzzy match)
        params = default_params
        if field:
            for field_key, field_params_val in field_params.items():
                if field_key.lower() in field.lower() or field.lower() in field_key.lower():
                    params = field_params_val
                    break
        
        # Adjust for publication year (older papers tend to have higher RCR)
        year_adjustment = 0.0
        if year and year < 2020:
            year_adjustment = (2020 - year) * 0.02  # 2% adjustment per year
        
        # Calculate log-normal percentile
        log_rcr = np.log(rcr)
        adjusted_log_rcr = log_rcr - year_adjustment
        
        # Standard normal CDF approximation
        z_score = (adjusted_log_rcr - params['mean_log_rcr']) / params['std_log_rcr']
        percentile = self._norm_cdf(z_score) * 100
        
        return min(99.9, max(0.1, percentile))
    
    def _norm_cdf(self, x: float) -> float:
        """Approximate standard normal CDF using error function.
        
        Args:
            x: Standard normal variable
            
        Returns:
            Cumulative probability
        """
        # Abramowitz and Stegun approximation
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        d = 0.3989423 * np.exp(-x * x / 2.0)
        prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.7814779 + t * (-1.8212560 + t * 1.3302744))))
        
        if x > 0:
            return 1.0 - prob
        else:
            return prob
    
    def calculate_field_impact_score(
        self, 
        paper: PaperRecord, 
        field_benchmarks: Optional[Dict] = None
    ) -> float:
        """Calculate comprehensive field-adjusted impact score.
        
        Combines citation metrics, RCR, and field position into single score.
        
        Args:
            paper: Paper record
            field_benchmarks: Optional field-specific benchmarks
            
        Returns:
            Field-adjusted impact score (0-100)
        """
        if not paper:
            return 0.0
        
        components = []
        weights = []
        
        # Citation count component (log-transformed)
        if paper.citation_count > 0:
            citation_score = min(100, np.log1p(paper.citation_count) * 15)
            components.append(citation_score)
            weights.append(0.3)
        
        # RCR component
        if paper.rcr and paper.rcr > 0:
            rcr_score = min(100, paper.rcr * 20)  # RCR of 5.0 = 100 points
            components.append(rcr_score)
            weights.append(0.4)
        
        # Percentile component
        if paper.percentile:
            components.append(paper.percentile)
            weights.append(0.2)
        
        # Independence component
        if paper.independent_citations is not None and paper.citation_count > 0:
            independence_ratio = paper.independent_citations / paper.citation_count
            independence_score = independence_ratio * 100
            components.append(independence_score)
            weights.append(0.1)
        
        if not components:
            return 0.0
        
        # Weighted average
        weighted_score = sum(c * w for c, w in zip(components, weights)) / sum(weights)
        
        return min(100, max(0, weighted_score))
    
    def normalize_citation_metrics(
        self, 
        papers: List[PaperRecord], 
        by_field: bool = True
    ) -> List[PaperRecord]:
        """Normalize citation metrics across papers.
        
        Args:
            papers: List of paper records
            by_field: Whether to normalize within fields
            
        Returns:
            List of papers with normalized metrics
        """
        if not papers:
            return papers
        
        # Group papers by field if requested
        if by_field:
            field_groups = defaultdict(list)
            for paper in papers:
                field = paper.primary_field or "Unknown"
                field_groups[field].append(paper)
            
            normalized_papers = []
            for field, field_papers in field_groups.items():
                normalized_papers.extend(self._normalize_field_group(field_papers))
            
            return normalized_papers
        else:
            return self._normalize_field_group(papers)
    
    def _normalize_field_group(self, papers: List[PaperRecord]) -> List[PaperRecord]:
        """Normalize metrics within a single field group.
        
        Args:
            papers: Papers from same field
            
        Returns:
            Papers with normalized metrics
        """
        if len(papers) < 2:
            return papers
        
        # Extract metrics
        citations = [p.citation_count for p in papers if p.citation_count is not None]
        rcrs = [p.rcr for p in papers if p.rcr is not None and p.rcr > 0]
        
        if not citations:
            return papers
        
        # Calculate field statistics
        citation_mean = np.mean(citations)
        citation_std = np.std(citations) if len(citations) > 1 else 1.0
        
        rcr_mean = np.mean(rcrs) if rcrs else 1.0
        rcr_std = np.std(rcrs) if len(rcrs) > 1 else 1.0
        
        # Normalize each paper
        normalized_papers = []
        for paper in papers:
            # Create copy to avoid modifying original
            normalized_paper = PaperRecord(**paper.model_dump())
            
            # Citation z-score
            if paper.citation_count is not None and citation_std > 0:
                citation_z = (paper.citation_count - citation_mean) / citation_std
                normalized_paper.citation_z_score = citation_z
                normalized_paper.citation_percentile = self._norm_cdf(citation_z) * 100
            
            # RCR z-score
            if paper.rcr is not None and paper.rcr > 0 and rcr_std > 0:
                rcr_z = (paper.rcr - rcr_mean) / rcr_std
                normalized_paper.rcr_z_score = rcr_z
            
            # Calculate field impact score
            normalized_paper.field_impact_score = self.calculate_field_impact_score(normalized_paper)
            
            normalized_papers.append(normalized_paper)
        
        return normalized_papers
    
    def identify_field_outliers(
        self, 
        papers: List[PaperRecord], 
        threshold: float = 2.0
    ) -> Dict[str, List[PaperRecord]]:
        """Identify papers that are outliers in their fields.
        
        Args:
            papers: List of paper records
            threshold: Z-score threshold for outlier detection
            
        Returns:
            Dictionary mapping field names to outlier papers
        """
        outliers = defaultdict(list)
        
        if not papers:
            return dict(outliers)
        
        # Group by field
        field_groups = defaultdict(list)
        for paper in papers:
            field = paper.primary_field or "Unknown"
            field_groups[field].append(paper)
        
        # Find outliers in each field
        for field, field_papers in field_groups.items():
            if len(field_papers) < 3:  # Need at least 3 papers for meaningful outlier detection
                continue
            
            citations = [p.citation_count for p in field_papers if p.citation_count is not None]
            if len(citations) < 3:
                continue
            
            mean_citations = np.mean(citations)
            std_citations = np.std(citations)
            
            if std_citations == 0:
                continue
            
            for paper in field_papers:
                if paper.citation_count is not None:
                    z_score = abs(paper.citation_count - mean_citations) / std_citations
                    if z_score > threshold:
                        outliers[field].append(paper)
        
        return dict(outliers)
    
    def calculate_field_rankings(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Calculate rankings within each field.
        
        Args:
            papers: List of paper records
            
        Returns:
            Dictionary with field rankings and statistics
        """
        if not papers:
            return {}
        
        # Group by field
        field_groups = defaultdict(list)
        for paper in papers:
            field = paper.primary_field or "Unknown"
            field_groups[field].append(paper)
        
        field_rankings = {}
        
        for field, field_papers in field_groups.items():
            # Sort by citation count
            sorted_papers = sorted(
                field_papers, 
                key=lambda p: p.citation_count or 0, 
                reverse=True
            )
            
            # Calculate rankings
            rankings = []
            for i, paper in enumerate(sorted_papers, 1):
                rank_info = {
                    'paper_id': paper.id,
                    'title': paper.title,
                    'citation_count': paper.citation_count,
                    'rank': i,
                    'percentile_rank': ((len(sorted_papers) - i) / len(sorted_papers)) * 100
                }
                rankings.append(rank_info)
            
            # Field statistics
            citations = [p.citation_count or 0 for p in field_papers]
            field_stats = {
                'total_papers': len(field_papers),
                'mean_citations': np.mean(citations),
                'median_citations': np.median(citations),
                'max_citations': max(citations),
                'min_citations': min(citations),
                'std_citations': np.std(citations),
                'total_citations': sum(citations)
            }
            
            field_rankings[field] = {
                'rankings': rankings,
                'statistics': field_stats
            }
        
        return field_rankings
    
    def create_field_comparison_matrix(self, papers: List[PaperRecord]) -> pd.DataFrame:
        """Create a matrix comparing metrics across fields.
        
        Args:
            papers: List of paper records
            
        Returns:
            DataFrame with field comparison metrics
        """
        if not papers:
            return pd.DataFrame()
        
        field_data = []
        
        # Group by field
        field_groups = defaultdict(list)
        for paper in papers:
            field = paper.primary_field or "Unknown"
            field_groups[field].append(paper)
        
        for field, field_papers in field_groups.items():
            citations = [p.citation_count or 0 for p in field_papers]
            rcrs = [p.rcr for p in field_papers if p.rcr is not None and p.rcr > 0]
            years = [p.year for p in field_papers if p.year is not None]
            
            field_metrics = {
                'field': field,
                'paper_count': len(field_papers),
                'total_citations': sum(citations),
                'mean_citations': np.mean(citations) if citations else 0,
                'median_citations': np.median(citations) if citations else 0,
                'max_citations': max(citations) if citations else 0,
                'h_index': self._calculate_h_index(citations),
                'mean_rcr': np.mean(rcrs) if rcrs else None,
                'median_rcr': np.median(rcrs) if rcrs else None,
                'papers_with_rcr': len(rcrs),
                'rcr_coverage': len(rcrs) / len(field_papers) if field_papers else 0,
                'year_range_start': min(years) if years else None,
                'year_range_end': max(years) if years else None,
                'papers_per_year': len(field_papers) / (max(years) - min(years) + 1) if years and len(set(years)) > 1 else None
            }
            
            field_data.append(field_metrics)
        
        if not field_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(field_data)
        df = df.sort_values('total_citations', ascending=False)
        
        return df
    
    def _calculate_h_index(self, citations: List[int]) -> int:
        """Calculate h-index for a list of citation counts.
        
        Args:
            citations: List of citation counts
            
        Returns:
            H-index value
        """
        if not citations:
            return 0
        
        sorted_citations = sorted(citations, reverse=True)
        h_index = 0
        
        for i, cite_count in enumerate(sorted_citations, 1):
            if cite_count >= i:
                h_index = i
            else:
                break
        
        return h_index 