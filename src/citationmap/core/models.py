"""Core data models for CitationMap."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator, model_validator


class FieldOfStudy(BaseModel):
    """Represents a field of study classification."""

    id: str
    display_name: str
    level: int
    score: float = Field(ge=0.0, le=1.0)


class Institution(BaseModel):
    """Represents an academic or research institution."""

    id: Optional[str] = None
    display_name: str
    country_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    type: Optional[str] = None


class Author(BaseModel):
    """Represents a paper author with affiliations."""

    id: Optional[str] = None
    display_name: str
    orcid: Optional[str] = None
    institutions: List[Institution] = []
    is_corresponding: bool = False


class CitationContext(str, Enum):
    """Types of citation contexts."""

    SELF_CITATION = "self_citation"
    INSTITUTIONAL_CITATION = "institutional_citation"
    INDEPENDENT_CITATION = "independent_citation"
    UNKNOWN = "unknown"


class Citation(BaseModel):
    """Represents a citation to a paper."""

    citing_paper_id: str
    citing_authors: List[Author] = []
    citing_institutions: List[Institution] = []
    citation_context: CitationContext = CitationContext.UNKNOWN
    year: Optional[int] = None


class PatentCitation(BaseModel):
    """Represents a patent that cites a research paper."""

    patent_id: str
    patent_title: str
    title: Optional[str] = None  # Alias for patent_title
    assignee: Optional[str] = None
    publication_date: Optional[datetime] = None
    year: Optional[int] = None
    classification: Optional[str] = None
    citation_context: Optional[CitationContext] = None
    citation_count: int = 0


class ClinicalTrial(BaseModel):
    """Represents a clinical trial that references a paper."""

    nct_id: str
    trial_id: Optional[str] = None  # Alias for nct_id
    title: str
    sponsor: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    condition: Optional[str] = None


class PaperRecord(BaseModel):
    """Represents a research paper with all associated metadata."""

    # Basic identifiers
    id: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    title: str
    authors: List[Author] = []

    # Publication details
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None
    venue: Optional[str] = None
    year: Optional[int] = None

    # Citation metrics
    citation_count: int = 0
    citations: List[Citation] = []
    independent_citations: int = 0
    self_citations: int = 0

    # Field classification
    fields_of_study: List[FieldOfStudy] = []
    primary_field: Optional[str] = None

    # Impact metrics
    rcr: Optional[float] = None  # Relative Citation Ratio
    fcr: Optional[float] = None  # Field Citation Ratio
    percentile: Optional[float] = None
    
    # Normalized metrics (computed by FieldNormalizer)
    citation_z_score: Optional[float] = None
    citation_percentile: Optional[float] = None
    rcr_z_score: Optional[float] = None
    field_impact_score: Optional[float] = None
    field_rank: Optional[int] = None
    field_percentile: Optional[float] = None

    # Downstream uptake
    patent_citations: List[PatentCitation] = []
    clinical_trials: List[ClinicalTrial] = []

    @model_validator(mode="after")
    def set_year_from_date(self):
        """Extract year from publication_date if year not provided."""
        if self.year is None and self.publication_date is not None:
            self.year = self.publication_date.year
        return self


class FieldMetrics(BaseModel):
    """Field-normalized metrics for comparison."""

    field_name: str
    total_papers: int
    median_citations: float
    top_10_percent_threshold: int
    top_1_percent_threshold: int


class AnalysisResult(BaseModel):
    """Results of citation analysis for a set of papers."""

    # Input metadata
    scholar_id: Optional[str] = None
    analysis_date: datetime = Field(default_factory=datetime.now)
    total_papers: int = 0

    # Analyzed papers
    papers: List[PaperRecord] = []

    # Aggregate metrics
    total_citations: int = 0
    total_independent_citations: int = 0
    h_index: int = 0
    i10_index: int = 0

    # Field-normalized metrics
    field_metrics: Dict[str, FieldMetrics] = {}
    papers_in_top_10_percent: int = 0
    papers_in_top_1_percent: int = 0

    # Geographic distribution
    citing_institutions: Dict[str, int] = {}  # country -> count
    citing_countries: Set[str] = set()

    # Downstream impact
    total_patent_citations: int = 0
    total_clinical_trials: int = 0

    @property
    def average_citations_per_paper(self) -> float:
        """Calculate average citations per paper."""
        if self.total_papers == 0:
            return 0.0
        return self.total_citations / self.total_papers

    @property
    def independence_ratio(self) -> float:
        """Calculate ratio of independent to total citations."""
        if self.total_citations == 0:
            return 0.0
        return self.total_independent_citations / self.total_citations

    def get_top_papers_by_citations(self, n: int = 10) -> List[PaperRecord]:
        """Get top N papers by citation count."""
        return sorted(self.papers, key=lambda p: p.citation_count, reverse=True)[:n]

    def get_papers_by_field(self, field_name: str) -> List[PaperRecord]:
        """Get papers in a specific field of study."""
        return [
            paper
            for paper in self.papers
            if any(
                field.display_name.lower() == field_name.lower()
                for field in paper.fields_of_study
            )
        ]
