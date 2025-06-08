"""Data merger for combining multiple API sources into canonical dataframes."""

import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import polars as pl
from datetime import datetime

from ..core.models import PaperRecord, AnalysisResult, Author, Institution, Citation
from ..data_acquisition import OpenAlexClient, iCiteClient

logger = logging.getLogger(__name__)


class DataMerger:
    """Merges data from multiple sources into canonical dataframes."""
    
    def __init__(self):
        """Initialize data merger."""
        self.logger = logger
    
    def papers_to_dataframe(self, papers: List[PaperRecord]) -> pd.DataFrame:
        """Convert PaperRecord objects to pandas DataFrame.
        
        Args:
            papers: List of PaperRecord objects
            
        Returns:
            Pandas DataFrame with paper data
        """
        if not papers:
            return pd.DataFrame()
        
        data = []
        for paper in papers:
            # Extract primary author and institution
            primary_author = paper.authors[0] if paper.authors else None
            primary_institution = None
            if primary_author and primary_author.institutions:
                primary_institution = primary_author.institutions[0]
            
            # Extract primary field
            primary_field = paper.primary_field
            if not primary_field and paper.fields_of_study:
                primary_field = paper.fields_of_study[0].display_name
            
            row = {
                'id': paper.id,
                'doi': paper.doi,
                'pmid': paper.pmid,
                'title': paper.title,
                'year': paper.year,
                'journal': paper.journal,
                'venue': paper.venue,
                'citation_count': paper.citation_count,
                'independent_citations': paper.independent_citations,
                'self_citations': paper.self_citations,
                'rcr': paper.rcr,
                'fcr': paper.fcr,
                'percentile': paper.percentile,
                'primary_field': primary_field,
                'num_authors': len(paper.authors),
                'num_fields': len(paper.fields_of_study),
                'patent_citations': len(paper.patent_citations),
                'clinical_trials': len(paper.clinical_trials),
                'primary_author_name': primary_author.display_name if primary_author else None,
                'primary_author_orcid': primary_author.orcid if primary_author else None,
                'primary_institution': primary_institution.display_name if primary_institution else None,
                'primary_institution_country': primary_institution.country_code if primary_institution else None,
                'publication_date': paper.publication_date
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Convert data types
        if not df.empty:
            df['year'] = pd.to_numeric(df['year'], errors='coerce')
            df['citation_count'] = pd.to_numeric(df['citation_count'], errors='coerce')
            df['independent_citations'] = pd.to_numeric(df['independent_citations'], errors='coerce')
            df['self_citations'] = pd.to_numeric(df['self_citations'], errors='coerce')
            df['rcr'] = pd.to_numeric(df['rcr'], errors='coerce')
            df['fcr'] = pd.to_numeric(df['fcr'], errors='coerce')
            df['percentile'] = pd.to_numeric(df['percentile'], errors='coerce')
            df['publication_date'] = pd.to_datetime(df['publication_date'], errors='coerce')
        
        return df
    
    def papers_to_polars(self, papers: List[PaperRecord]) -> pl.DataFrame:
        """Convert PaperRecord objects to Polars DataFrame.
        
        Args:
            papers: List of PaperRecord objects
            
        Returns:
            Polars DataFrame with paper data
        """
        pandas_df = self.papers_to_dataframe(papers)
        if pandas_df.empty:
            return pl.DataFrame()
        
        return pl.from_pandas(pandas_df)
    
    def merge_icite_data(
        self, 
        papers_df: pd.DataFrame, 
        icite_data: Dict[str, Dict[str, Any]]
    ) -> pd.DataFrame:
        """Merge iCite metrics into papers dataframe.
        
        Args:
            papers_df: DataFrame with paper data
            icite_data: Dictionary mapping DOI/PMID to iCite metrics
            
        Returns:
            DataFrame with iCite metrics merged
        """
        if papers_df.empty or not icite_data:
            return papers_df
        
        # Create iCite lookup by DOI
        icite_rows = []
        for identifier, metrics in icite_data.items():
            if isinstance(metrics, dict):
                icite_rows.append({
                    'lookup_id': identifier,
                    'icite_rcr': metrics.get('relative_citation_ratio'),
                    'icite_fcr': metrics.get('field_citation_rate'),
                    'icite_citations': metrics.get('citation_count'),
                    'icite_provisional': metrics.get('provisional', True),
                    'icite_year': metrics.get('year')
                })
        
        if not icite_rows:
            return papers_df
        
        icite_df = pd.DataFrame(icite_rows)
        
        # Merge by DOI first, then by PMID if available
        result_df = papers_df.copy()
        
        # Merge by DOI
        doi_merge = result_df.merge(
            icite_df, 
            left_on='doi', 
            right_on='lookup_id', 
            how='left',
            suffixes=('', '_icite')
        )
        
        # Update RCR/FCR with iCite data where available
        doi_merge['rcr'] = doi_merge['icite_rcr'].fillna(doi_merge['rcr'])
        doi_merge['fcr'] = doi_merge['icite_fcr'].fillna(doi_merge['fcr'])
        
        # Drop temporary columns
        cols_to_drop = [col for col in doi_merge.columns if col.startswith('icite_') or col == 'lookup_id']
        result_df = doi_merge.drop(columns=cols_to_drop, errors='ignore')
        
        return result_df
    
    def create_citations_dataframe(self, papers: List[PaperRecord]) -> pd.DataFrame:
        """Create a dataframe of all citations across papers.
        
        Args:
            papers: List of PaperRecord objects
            
        Returns:
            DataFrame with citation data
        """
        citation_data = []
        
        for paper in papers:
            for citation in paper.citations:
                # Extract citing author info
                citing_authors = [author.display_name for author in citation.citing_authors]
                citing_institutions = [inst.display_name for inst in citation.citing_institutions]
                citing_countries = [inst.country_code for inst in citation.citing_institutions if inst.country_code]
                
                row = {
                    'cited_paper_id': paper.id,
                    'cited_paper_title': paper.title,
                    'citing_paper_id': citation.citing_paper_id,
                    'citation_context': citation.citation_context.value,
                    'citing_year': citation.year,
                    'citing_authors': '; '.join(citing_authors),
                    'citing_institutions': '; '.join(citing_institutions),
                    'citing_countries': '; '.join(citing_countries),
                    'num_citing_authors': len(citation.citing_authors),
                    'num_citing_institutions': len(citation.citing_institutions)
                }
                citation_data.append(row)
        
        if not citation_data:
            return pd.DataFrame()
        
        citations_df = pd.DataFrame(citation_data)
        
        # Convert data types
        citations_df['citing_year'] = pd.to_numeric(citations_df['citing_year'], errors='coerce')
        
        return citations_df
    
    def create_institutions_dataframe(self, papers: List[PaperRecord]) -> pd.DataFrame:
        """Create a dataframe of all institutions across papers.
        
        Args:
            papers: List of PaperRecord objects
            
        Returns:
            DataFrame with institution data
        """
        institution_data = []
        
        for paper in papers:
            for author in paper.authors:
                for institution in author.institutions:
                    row = {
                        'paper_id': paper.id,
                        'paper_title': paper.title,
                        'author_name': author.display_name,
                        'author_orcid': author.orcid,
                        'institution_id': institution.id,
                        'institution_name': institution.display_name,
                        'institution_country': institution.country_code,
                        'institution_type': institution.type,
                        'institution_latitude': institution.latitude,
                        'institution_longitude': institution.longitude,
                        'is_corresponding': author.is_corresponding
                    }
                    institution_data.append(row)
        
        if not institution_data:
            return pd.DataFrame()
        
        institutions_df = pd.DataFrame(institution_data)
        
        # Convert data types
        institutions_df['institution_latitude'] = pd.to_numeric(institutions_df['institution_latitude'], errors='coerce')
        institutions_df['institution_longitude'] = pd.to_numeric(institutions_df['institution_longitude'], errors='coerce')
        
        return institutions_df
    
    def aggregate_field_metrics(self, papers_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate metrics by field of study.
        
        Args:
            papers_df: DataFrame with paper data
            
        Returns:
            DataFrame with field-level aggregated metrics
        """
        if papers_df.empty or 'primary_field' not in papers_df.columns:
            return pd.DataFrame()
        
        # Filter out papers without field information
        field_df = papers_df[papers_df['primary_field'].notna()].copy()
        
        if field_df.empty:
            return pd.DataFrame()
        
        # Group by field and calculate metrics
        field_metrics = field_df.groupby('primary_field').agg({
            'citation_count': ['count', 'sum', 'mean', 'median', 'std'],
            'independent_citations': ['sum', 'mean'],
            'rcr': ['mean', 'median'],
            'year': ['min', 'max', 'mean'],
            'patent_citations': 'sum',
            'clinical_trials': 'sum'
        }).reset_index()
        
        # Flatten column names
        field_metrics.columns = [
            'field_name', 
            'paper_count', 'total_citations', 'mean_citations', 'median_citations', 'std_citations',
            'total_independent_citations', 'mean_independent_citations',
            'mean_rcr', 'median_rcr',
            'earliest_year', 'latest_year', 'mean_year',
            'total_patent_citations', 'total_clinical_trials'
        ]
        
        # Calculate percentile thresholds
        field_metrics['top_10_percent_threshold'] = field_df.groupby('primary_field')['citation_count'].quantile(0.9).values
        field_metrics['top_1_percent_threshold'] = field_df.groupby('primary_field')['citation_count'].quantile(0.99).values
        
        return field_metrics
    
    def create_analysis_summary(
        self, 
        papers: List[PaperRecord],
        field_metrics_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Create a comprehensive analysis summary.
        
        Args:
            papers: List of PaperRecord objects
            field_metrics_df: Optional field metrics dataframe
            
        Returns:
            Dictionary with analysis summary
        """
        if not papers:
            return {}
        
        papers_df = self.papers_to_dataframe(papers)
        
        # Basic metrics
        total_papers = len(papers)
        total_citations = papers_df['citation_count'].sum()
        total_independent = papers_df['independent_citations'].sum()
        
        # H-index calculation
        sorted_citations = sorted([p.citation_count for p in papers], reverse=True)
        h_index = 0
        for i, citations in enumerate(sorted_citations, 1):
            if citations >= i:
                h_index = i
            else:
                break
        
        # i10-index (papers with >=10 citations)
        i10_index = sum(1 for p in papers if p.citation_count >= 10)
        
        # Field distribution
        field_counts = papers_df['primary_field'].value_counts().to_dict() if not papers_df.empty else {}
        
        # Geographic distribution
        institutions_df = self.create_institutions_dataframe(papers)
        country_counts = institutions_df['institution_country'].value_counts().to_dict() if not institutions_df.empty else {}
        
        summary = {
            'total_papers': total_papers,
            'total_citations': int(total_citations) if pd.notna(total_citations) else 0,
            'total_independent_citations': int(total_independent) if pd.notna(total_independent) else 0,
            'h_index': h_index,
            'i10_index': i10_index,
            'average_citations_per_paper': total_citations / total_papers if total_papers > 0 else 0.0,
            'independence_ratio': total_independent / total_citations if total_citations > 0 else 0.0,
            'field_distribution': field_counts,
            'country_distribution': country_counts,
            'year_range': {
                'earliest': int(papers_df['year'].min()) if not papers_df.empty and pd.notna(papers_df['year'].min()) else None,
                'latest': int(papers_df['year'].max()) if not papers_df.empty and pd.notna(papers_df['year'].max()) else None
            },
            'analysis_date': datetime.now().isoformat()
        }
        
        return summary 