"""Downstream uptake aggregator for patents, clinical trials, and guidelines."""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

from ..core.models import PaperRecord, PatentCitation, ClinicalTrial

logger = logging.getLogger(__name__)


class UptakeAggregator:
    """Aggregates and analyzes downstream uptake of research papers."""
    
    def __init__(self):
        """Initialize uptake aggregator."""
        self.logger = logger
    
    def analyze_patent_uptake(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Analyze patent citations and technology transfer.
        
        Args:
            papers: List of paper records
            
        Returns:
            Dictionary with patent uptake analysis
        """
        if not papers:
            return {}
        
        # Collect all patent citations
        all_patents = []
        papers_with_patents = 0
        
        for paper in papers:
            if paper.patent_citations:
                papers_with_patents += 1
                for patent in paper.patent_citations:
                    patent_info = {
                        'paper_id': paper.id,
                        'paper_title': paper.title,
                        'paper_year': paper.year,
                        'primary_field': paper.primary_field,
                        'patent_id': patent.patent_id,
                        'patent_title': patent.title,
                        'patent_year': patent.year,
                        'patent_assignee': patent.assignee,
                        'patent_classification': patent.classification,
                        'citation_context': patent.citation_context.value if patent.citation_context else None
                    }
                    all_patents.append(patent_info)
        
        if not all_patents:
            return {
                'total_papers': len(papers),
                'papers_with_patents': 0,
                'patent_citation_rate': 0.0,
                'total_patent_citations': 0
            }
        
        patents_df = pd.DataFrame(all_patents)
        
        # Basic statistics
        total_patent_citations = len(all_patents)
        patent_citation_rate = papers_with_patents / len(papers)
        
        # Time analysis
        time_to_patent = []
        for _, row in patents_df.iterrows():
            if row['paper_year'] and row['patent_year']:
                time_diff = row['patent_year'] - row['paper_year']
                if time_diff >= 0:  # Only consider forward citations
                    time_to_patent.append(time_diff)
        
        avg_time_to_patent = sum(time_to_patent) / len(time_to_patent) if time_to_patent else None
        
        # Field analysis
        field_patent_counts = patents_df.groupby('primary_field').size().to_dict() if 'primary_field' in patents_df.columns else {}
        
        # Assignee analysis
        assignee_counts = patents_df['patent_assignee'].value_counts().head(10).to_dict() if 'patent_assignee' in patents_df.columns else {}
        
        # Classification analysis
        classification_counts = Counter()
        for classification in patents_df['patent_classification'].dropna():
            if isinstance(classification, str):
                # Extract main classification code (first part before /)
                main_class = classification.split('/')[0] if '/' in classification else classification
                classification_counts[main_class] += 1
        
        analysis = {
            'total_papers': len(papers),
            'papers_with_patents': papers_with_patents,
            'patent_citation_rate': patent_citation_rate,
            'total_patent_citations': total_patent_citations,
            'average_patents_per_paper': total_patent_citations / len(papers),
            'average_time_to_patent': avg_time_to_patent,
            'field_distribution': field_patent_counts,
            'top_assignees': assignee_counts,
            'top_classifications': dict(classification_counts.most_common(10)),
            'patent_timeline': self._create_patent_timeline(patents_df),
            'high_patent_impact_papers': self._identify_high_patent_impact_papers(papers)
        }
        
        return analysis
    
    def analyze_clinical_trial_uptake(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Analyze clinical trial citations and medical impact.
        
        Args:
            papers: List of paper records
            
        Returns:
            Dictionary with clinical trial uptake analysis
        """
        if not papers:
            return {}
        
        # Collect all clinical trial citations
        all_trials = []
        papers_with_trials = 0
        
        for paper in papers:
            if paper.clinical_trials:
                papers_with_trials += 1
                for trial in paper.clinical_trials:
                    trial_info = {
                        'paper_id': paper.id,
                        'paper_title': paper.title,
                        'paper_year': paper.year,
                        'primary_field': paper.primary_field,
                        'trial_id': trial.trial_id,
                        'trial_title': trial.title,
                        'trial_status': trial.status,
                        'trial_phase': trial.phase,
                        'trial_start_date': trial.start_date,
                        'trial_sponsor': trial.sponsor,
                        'trial_condition': trial.condition
                    }
                    all_trials.append(trial_info)
        
        if not all_trials:
            return {
                'total_papers': len(papers),
                'papers_with_trials': 0,
                'trial_citation_rate': 0.0,
                'total_trial_citations': 0
            }
        
        trials_df = pd.DataFrame(all_trials)
        
        # Basic statistics
        total_trial_citations = len(all_trials)
        trial_citation_rate = papers_with_trials / len(papers)
        
        # Phase analysis
        phase_counts = trials_df['trial_phase'].value_counts().to_dict() if 'trial_phase' in trials_df.columns else {}
        
        # Status analysis
        status_counts = trials_df['trial_status'].value_counts().to_dict() if 'trial_status' in trials_df.columns else {}
        
        # Condition analysis
        condition_counts = trials_df['trial_condition'].value_counts().head(10).to_dict() if 'trial_condition' in trials_df.columns else {}
        
        # Sponsor analysis
        sponsor_counts = trials_df['trial_sponsor'].value_counts().head(10).to_dict() if 'trial_sponsor' in trials_df.columns else {}
        
        # Time analysis
        time_to_trial = []
        for _, row in trials_df.iterrows():
            if row['paper_year'] and row['trial_start_date']:
                try:
                    if isinstance(row['trial_start_date'], str):
                        trial_year = int(row['trial_start_date'][:4])
                    else:
                        trial_year = row['trial_start_date'].year
                    
                    time_diff = trial_year - row['paper_year']
                    if time_diff >= 0:  # Only consider forward citations
                        time_to_trial.append(time_diff)
                except (ValueError, AttributeError):
                    continue
        
        avg_time_to_trial = sum(time_to_trial) / len(time_to_trial) if time_to_trial else None
        
        analysis = {
            'total_papers': len(papers),
            'papers_with_trials': papers_with_trials,
            'trial_citation_rate': trial_citation_rate,
            'total_trial_citations': total_trial_citations,
            'average_trials_per_paper': total_trial_citations / len(papers),
            'average_time_to_trial': avg_time_to_trial,
            'phase_distribution': phase_counts,
            'status_distribution': status_counts,
            'top_conditions': condition_counts,
            'top_sponsors': sponsor_counts,
            'trial_timeline': self._create_trial_timeline(trials_df),
            'high_clinical_impact_papers': self._identify_high_clinical_impact_papers(papers)
        }
        
        return analysis
    
    def analyze_policy_uptake(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Analyze policy and guideline uptake.
        
        Note: This is a placeholder for future implementation when
        policy/guideline data sources are integrated.
        
        Args:
            papers: List of paper records
            
        Returns:
            Dictionary with policy uptake analysis
        """
        # Placeholder implementation
        # In the future, this would analyze citations in:
        # - Clinical practice guidelines
        # - Government policy documents
        # - Professional society recommendations
        # - Regulatory submissions
        
        return {
            'total_papers': len(papers),
            'policy_implementation_status': 'not_implemented',
            'note': 'Policy uptake analysis requires integration with policy databases'
        }
    
    def calculate_translational_impact_score(self, paper: PaperRecord) -> float:
        """Calculate a comprehensive translational impact score.
        
        Combines patent citations, clinical trials, and other translational metrics.
        
        Args:
            paper: Paper record
            
        Returns:
            Translational impact score (0-100)
        """
        if not paper:
            return 0.0
        
        components = []
        weights = []
        
        # Patent component
        patent_count = len(paper.patent_citations)
        if patent_count > 0:
            # Log scale for patents (each patent adds diminishing value)
            patent_score = min(100, patent_count * 20 + (patent_count - 1) * 5)
            components.append(patent_score)
            weights.append(0.4)
        
        # Clinical trial component
        trial_count = len(paper.clinical_trials)
        if trial_count > 0:
            # Higher weight for clinical trials as they're rarer and more impactful
            trial_score = min(100, trial_count * 30 + (trial_count - 1) * 10)
            components.append(trial_score)
            weights.append(0.5)
        
        # Citation impact component
        if paper.citation_count and paper.citation_count > 0:
            # Citation component with logarithmic scaling
            citation_score = min(50, np.log1p(paper.citation_count) * 8)
            components.append(citation_score)
            weights.append(0.1)
        
        if not components:
            return 0.0
        
        # Weighted average
        weighted_score = sum(c * w for c, w in zip(components, weights)) / sum(weights)
        
        return min(100, max(0, weighted_score))
    
    def create_uptake_timeline(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Create timeline of downstream uptake events.
        
        Args:
            papers: List of paper records
            
        Returns:
            Dictionary with timeline data
        """
        timeline_events = []
        
        for paper in papers:
            paper_year = paper.year or datetime.now().year
            
            # Add publication event
            timeline_events.append({
                'date': paper_year,
                'type': 'publication',
                'paper_id': paper.id,
                'paper_title': paper.title,
                'event_title': f"Published: {paper.title[:50]}..."
            })
            
            # Add patent events
            for patent in paper.patent_citations:
                if patent.year:
                    timeline_events.append({
                        'date': patent.year,
                        'type': 'patent',
                        'paper_id': paper.id,
                        'patent_id': patent.patent_id,
                        'event_title': f"Patent: {patent.title[:50]}..." if patent.title else f"Patent {patent.patent_id}"
                    })
            
            # Add clinical trial events
            for trial in paper.clinical_trials:
                if trial.start_date:
                    try:
                        if isinstance(trial.start_date, str):
                            trial_year = int(trial.start_date[:4])
                        else:
                            trial_year = trial.start_date.year
                        
                        timeline_events.append({
                            'date': trial_year,
                            'type': 'clinical_trial',
                            'paper_id': paper.id,
                            'trial_id': trial.trial_id,
                            'event_title': f"Clinical Trial: {trial.title[:50]}..." if trial.title else f"Trial {trial.trial_id}"
                        })
                    except (ValueError, AttributeError):
                        continue
        
        # Sort by date
        timeline_events.sort(key=lambda x: x['date'])
        
        # Create summary statistics
        event_counts = Counter(event['type'] for event in timeline_events)
        
        return {
            'timeline_events': timeline_events,
            'event_counts': dict(event_counts),
            'date_range': {
                'start': min(event['date'] for event in timeline_events) if timeline_events else None,
                'end': max(event['date'] for event in timeline_events) if timeline_events else None
            }
        }
    
    def identify_breakthrough_papers(self, papers: List[PaperRecord], threshold: float = 80.0) -> List[Dict[str, Any]]:
        """Identify papers with exceptional translational impact.
        
        Args:
            papers: List of paper records
            threshold: Minimum translational impact score threshold
            
        Returns:
            List of breakthrough papers with their impact metrics
        """
        breakthrough_papers = []
        
        for paper in papers:
            impact_score = self.calculate_translational_impact_score(paper)
            
            if impact_score >= threshold:
                paper_info = {
                    'id': paper.id,
                    'title': paper.title,
                    'year': paper.year,
                    'citation_count': paper.citation_count,
                    'patent_citations': len(paper.patent_citations),
                    'clinical_trials': len(paper.clinical_trials),
                    'translational_impact_score': impact_score,
                    'primary_field': paper.primary_field,
                    'breakthrough_factors': self._identify_breakthrough_factors(paper)
                }
                breakthrough_papers.append(paper_info)
        
        # Sort by impact score
        breakthrough_papers.sort(key=lambda x: x['translational_impact_score'], reverse=True)
        
        return breakthrough_papers
    
    def generate_uptake_report(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Generate comprehensive uptake analysis report.
        
        Args:
            papers: List of paper records
            
        Returns:
            Comprehensive uptake report
        """
        patent_analysis = self.analyze_patent_uptake(papers)
        trial_analysis = self.analyze_clinical_trial_uptake(papers)
        policy_analysis = self.analyze_policy_uptake(papers)
        timeline = self.create_uptake_timeline(papers)
        breakthrough_papers = self.identify_breakthrough_papers(papers)
        
        # Calculate overall translational metrics
        translational_scores = [
            self.calculate_translational_impact_score(paper) 
            for paper in papers
        ]
        
        avg_translational_score = sum(translational_scores) / len(translational_scores) if translational_scores else 0
        
        # Papers with any translational impact
        papers_with_translational_impact = sum(
            1 for paper in papers 
            if len(paper.patent_citations) > 0 or len(paper.clinical_trials) > 0
        )
        
        translational_rate = papers_with_translational_impact / len(papers) if papers else 0
        
        report = {
            'executive_summary': {
                'total_papers': len(papers),
                'papers_with_translational_impact': papers_with_translational_impact,
                'translational_impact_rate': translational_rate,
                'average_translational_score': avg_translational_score,
                'breakthrough_papers_count': len(breakthrough_papers)
            },
            'patent_analysis': patent_analysis,
            'clinical_trial_analysis': trial_analysis,
            'policy_analysis': policy_analysis,
            'timeline': timeline,
            'breakthrough_papers': breakthrough_papers,
            'recommendations': self._generate_uptake_recommendations(papers, patent_analysis, trial_analysis),
            'translational_potential': self._assess_translational_potential(papers)
        }
        
        return report
    
    def _create_patent_timeline(self, patents_df: pd.DataFrame) -> Dict[str, Any]:
        """Create patent citation timeline."""
        if patents_df.empty:
            return {}
        
        # Group patents by year
        yearly_counts = patents_df.groupby('patent_year').size().to_dict()
        
        return {
            'yearly_patent_counts': yearly_counts,
            'patent_growth_trend': self._calculate_growth_trend(yearly_counts)
        }
    
    def _create_trial_timeline(self, trials_df: pd.DataFrame) -> Dict[str, Any]:
        """Create clinical trial timeline."""
        if trials_df.empty:
            return {}
        
        # Extract years from start dates
        trial_years = []
        for start_date in trials_df['trial_start_date'].dropna():
            try:
                if isinstance(start_date, str):
                    year = int(start_date[:4])
                else:
                    year = start_date.year
                trial_years.append(year)
            except (ValueError, AttributeError):
                continue
        
        yearly_counts = Counter(trial_years)
        
        return {
            'yearly_trial_counts': dict(yearly_counts),
            'trial_growth_trend': self._calculate_growth_trend(dict(yearly_counts))
        }
    
    def _calculate_growth_trend(self, yearly_counts: Dict[int, int]) -> str:
        """Calculate growth trend from yearly counts."""
        if len(yearly_counts) < 2:
            return "insufficient_data"
        
        years = sorted(yearly_counts.keys())
        counts = [yearly_counts[year] for year in years]
        
        # Simple linear trend
        if len(counts) >= 3:
            recent_avg = sum(counts[-3:]) / 3
            early_avg = sum(counts[:3]) / 3 if len(counts) >= 6 else sum(counts[:-3]) / len(counts[:-3])
            
            if recent_avg > early_avg * 1.2:
                return "increasing"
            elif recent_avg < early_avg * 0.8:
                return "decreasing"
            else:
                return "stable"
        
        return "unknown"
    
    def _identify_high_patent_impact_papers(self, papers: List[PaperRecord]) -> List[Dict[str, Any]]:
        """Identify papers with high patent impact."""
        high_impact = []
        
        for paper in papers:
            patent_count = len(paper.patent_citations)
            if patent_count >= 3:  # Threshold for high patent impact
                high_impact.append({
                    'id': paper.id,
                    'title': paper.title,
                    'patent_count': patent_count,
                    'citation_count': paper.citation_count
                })
        
        return sorted(high_impact, key=lambda x: x['patent_count'], reverse=True)
    
    def _identify_high_clinical_impact_papers(self, papers: List[PaperRecord]) -> List[Dict[str, Any]]:
        """Identify papers with high clinical impact."""
        high_impact = []
        
        for paper in papers:
            trial_count = len(paper.clinical_trials)
            if trial_count >= 2:  # Threshold for high clinical impact
                high_impact.append({
                    'id': paper.id,
                    'title': paper.title,
                    'trial_count': trial_count,
                    'citation_count': paper.citation_count
                })
        
        return sorted(high_impact, key=lambda x: x['trial_count'], reverse=True)
    
    def _identify_breakthrough_factors(self, paper: PaperRecord) -> List[str]:
        """Identify factors that make a paper a breakthrough."""
        factors = []
        
        if len(paper.patent_citations) >= 5:
            factors.append("high_patent_impact")
        
        if len(paper.clinical_trials) >= 3:
            factors.append("high_clinical_impact")
        
        if paper.citation_count and paper.citation_count >= 100:
            factors.append("high_citation_impact")
        
        if paper.rcr and paper.rcr >= 5.0:
            factors.append("exceptional_field_impact")
        
        # Check for rapid uptake (patents/trials within 2 years)
        paper_year = paper.year or datetime.now().year
        rapid_patents = sum(
            1 for patent in paper.patent_citations
            if patent.year and patent.year - paper_year <= 2
        )
        
        if rapid_patents >= 2:
            factors.append("rapid_patent_uptake")
        
        return factors
    
    def _generate_uptake_recommendations(
        self, 
        papers: List[PaperRecord], 
        patent_analysis: Dict[str, Any],
        trial_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving translational impact."""
        recommendations = []
        
        if not papers:
            return recommendations
        
        patent_rate = patent_analysis.get('patent_citation_rate', 0)
        trial_rate = trial_analysis.get('trial_citation_rate', 0)
        
        if patent_rate < 0.1:
            recommendations.append(
                "Consider collaborating with industry partners or filing provisional patents "
                "to increase technology transfer potential."
            )
        
        if trial_rate < 0.05:
            recommendations.append(
                "For clinical research, engage with clinical trial networks and "
                "medical professionals to facilitate translation to practice."
            )
        
        if patent_rate > 0.3:
            recommendations.append(
                f"Strong patent uptake rate of {patent_rate:.1%}. Continue focus on "
                "applied research with commercial potential."
            )
        
        if trial_rate > 0.2:
            recommendations.append(
                f"Excellent clinical trial integration rate of {trial_rate:.1%}. "
                "This demonstrates strong clinical relevance."
            )
        
        # Field-specific recommendations
        field_patterns = defaultdict(list)
        for paper in papers:
            field = paper.primary_field or "Unknown"
            translational_score = self.calculate_translational_impact_score(paper)
            field_patterns[field].append(translational_score)
        
        for field, scores in field_patterns.items():
            if len(scores) >= 3:
                avg_score = sum(scores) / len(scores)
                if avg_score < 20:
                    recommendations.append(
                        f"In {field}, consider more applied research directions "
                        "to increase translational potential."
                    )
        
        return recommendations
    
    def _assess_translational_potential(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Assess future translational potential of the research portfolio."""
        recent_papers = [
            paper for paper in papers 
            if paper.year and paper.year >= datetime.now().year - 3
        ]
        
        if not recent_papers:
            return {'status': 'insufficient_recent_data'}
        
        recent_translational_scores = [
            self.calculate_translational_impact_score(paper) 
            for paper in recent_papers
        ]
        
        avg_recent_score = sum(recent_translational_scores) / len(recent_translational_scores)
        
        # Assess based on field and recency
        clinical_fields = ['medicine', 'biology', 'biomedical', 'health', 'clinical']
        applied_fields = ['engineering', 'computer science', 'technology']
        
        field_alignment_score = 0
        for paper in recent_papers:
            field = paper.primary_field.lower() if paper.primary_field else ""
            if any(clinical_field in field for clinical_field in clinical_fields):
                field_alignment_score += 30
            elif any(applied_field in field for applied_field in applied_fields):
                field_alignment_score += 20
            else:
                field_alignment_score += 10
        
        field_alignment_score = min(100, field_alignment_score / len(recent_papers))
        
        potential_score = (avg_recent_score * 0.7) + (field_alignment_score * 0.3)
        
        if potential_score >= 70:
            potential_level = "high"
        elif potential_score >= 40:
            potential_level = "moderate"
        else:
            potential_level = "low"
        
        return {
            'potential_level': potential_level,
            'potential_score': potential_score,
            'recent_papers_count': len(recent_papers),
            'average_recent_translational_score': avg_recent_score,
            'field_alignment_score': field_alignment_score
        } 