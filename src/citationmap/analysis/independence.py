"""Independence classifier for distinguishing self-citations from independent citations."""

import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from ..core.models import Author, Citation, Institution, PaperRecord

logger = logging.getLogger(__name__)


class IndependenceClassifier:
    """Classifies citations as self-citations or independent citations."""

    def __init__(
        self,
        author_similarity_threshold: float = 0.8,
        institution_similarity_threshold: float = 0.9,
    ):
        """Initialize independence classifier.

        Args:
            author_similarity_threshold: Threshold for author name matching
            institution_similarity_threshold: Threshold for institution name matching
        """
        self.logger = logger
        self.author_threshold = author_similarity_threshold
        self.institution_threshold = institution_similarity_threshold

        # Cache for author and institution normalizations
        self.author_cache = {}
        self.institution_cache = {}

    def classify_citations(self, papers: List[PaperRecord]) -> List[PaperRecord]:
        """Classify all citations in the papers as self or independent.

        Args:
            papers: List of paper records with citations

        Returns:
            Papers with classified citations
        """
        if not papers:
            return papers

        # Build author and institution networks
        author_network = self._build_author_network(papers)
        institution_network = self._build_institution_network(papers)

        classified_papers = []

        for paper in papers:
            classified_paper = PaperRecord(**paper.model_dump())

            # Classify each citation
            independent_count = 0
            self_count = 0

            for citation in paper.citations:
                is_independent = self._is_independent_citation(
                    paper, citation, author_network, institution_network
                )

                if is_independent:
                    independent_count += 1
                else:
                    self_count += 1

            # Update counts
            classified_paper.independent_citations = independent_count
            classified_paper.self_citations = self_count

            classified_papers.append(classified_paper)

        return classified_papers

    def _build_author_network(self, papers: List[PaperRecord]) -> Dict[str, Set[str]]:
        """Build network of author connections across papers.

        Args:
            papers: List of paper records

        Returns:
            Dictionary mapping normalized author names to sets of connected authors
        """
        author_network = defaultdict(set)

        for paper in papers:
            # Normalize author names
            normalized_authors = []
            for author in paper.authors:
                normalized_name = self._normalize_author_name(author.display_name)
                normalized_authors.append(normalized_name)

                # Also store ORCID mappings if available
                if author.orcid:
                    author_network[normalized_name].add(f"orcid:{author.orcid}")

            # Connect all co-authors
            for i, author1 in enumerate(normalized_authors):
                for j, author2 in enumerate(normalized_authors):
                    if i != j:
                        author_network[author1].add(author2)
                        author_network[author2].add(author1)

        return dict(author_network)

    def _build_institution_network(
        self, papers: List[PaperRecord]
    ) -> Dict[str, Set[str]]:
        """Build network of institutional connections.

        Args:
            papers: List of paper records

        Returns:
            Dictionary mapping normalized institution names to connected institutions
        """
        institution_network = defaultdict(set)

        for paper in papers:
            institutions = set()

            # Collect all institutions from all authors
            for author in paper.authors:
                for institution in author.institutions:
                    normalized_name = self._normalize_institution_name(
                        institution.display_name
                    )
                    institutions.add(normalized_name)

            # Connect institutions that appear on the same paper
            institution_list = list(institutions)
            for i, inst1 in enumerate(institution_list):
                for j, inst2 in enumerate(institution_list):
                    if i != j:
                        institution_network[inst1].add(inst2)
                        institution_network[inst2].add(inst1)

        return dict(institution_network)

    def _is_independent_citation(
        self,
        cited_paper: PaperRecord,
        citation: Citation,
        author_network: Dict[str, Set[str]],
        institution_network: Dict[str, Set[str]],
    ) -> bool:
        """Determine if a citation is independent or self-citation.

        Args:
            cited_paper: The paper being cited
            citation: The citation object
            author_network: Author connection network
            institution_network: Institution connection network

        Returns:
            True if independent citation, False if self-citation
        """
        # Check author overlap
        if self._has_author_overlap(cited_paper, citation, author_network):
            return False

        # Check institution overlap
        if self._has_institution_overlap(cited_paper, citation, institution_network):
            return False

        # Check for close collaborator relationships
        if self._has_close_collaborator_overlap(cited_paper, citation, author_network):
            return False

        return True

    def _has_author_overlap(
        self,
        cited_paper: PaperRecord,
        citation: Citation,
        author_network: Dict[str, Set[str]],
    ) -> bool:
        """Check if there's author overlap between cited and citing papers.

        Args:
            cited_paper: The cited paper
            citation: The citation
            author_network: Author network

        Returns:
            True if there's author overlap
        """
        # Normalize cited paper authors
        cited_authors = {
            self._normalize_author_name(author.display_name)
            for author in cited_paper.authors
        }

        # Normalize citing paper authors
        citing_authors = {
            self._normalize_author_name(author.display_name)
            for author in citation.citing_authors
        }

        # Direct overlap check
        if cited_authors & citing_authors:
            return True

        # Check for similar author names (accounting for name variations)
        for cited_author in cited_authors:
            for citing_author in citing_authors:
                if self._are_similar_authors(cited_author, citing_author):
                    return True

        return False

    def _has_institution_overlap(
        self,
        cited_paper: PaperRecord,
        citation: Citation,
        institution_network: Dict[str, Set[str]],
    ) -> bool:
        """Check if there's institutional overlap.

        Args:
            cited_paper: The cited paper
            citation: The citation
            institution_network: Institution network

        Returns:
            True if there's institutional overlap
        """
        # Collect cited paper institutions
        cited_institutions = set()
        for author in cited_paper.authors:
            for institution in author.institutions:
                normalized = self._normalize_institution_name(institution.display_name)
                cited_institutions.add(normalized)

        # Collect citing paper institutions
        citing_institutions = set()
        for institution in citation.citing_institutions:
            normalized = self._normalize_institution_name(institution.display_name)
            citing_institutions.add(normalized)

        # Direct overlap check
        if cited_institutions & citing_institutions:
            return True

        # Check for similar institution names
        for cited_inst in cited_institutions:
            for citing_inst in citing_institutions:
                if self._are_similar_institutions(cited_inst, citing_inst):
                    return True

        return False

    def _has_close_collaborator_overlap(
        self,
        cited_paper: PaperRecord,
        citation: Citation,
        author_network: Dict[str, Set[str]],
    ) -> bool:
        """Check for close collaborator relationships.

        Args:
            cited_paper: The cited paper
            citation: The citation
            author_network: Author network

        Returns:
            True if citing authors are close collaborators of cited authors
        """
        # This is a more sophisticated check for frequent collaborators
        # For now, implement a simple version

        cited_authors = {
            self._normalize_author_name(author.display_name)
            for author in cited_paper.authors
        }

        citing_authors = {
            self._normalize_author_name(author.display_name)
            for author in citation.citing_authors
        }

        # Check if any citing author is in the direct network of cited authors
        for cited_author in cited_authors:
            if cited_author in author_network:
                connected_authors = author_network[cited_author]
                if connected_authors & citing_authors:
                    return True

        return False

    def _normalize_author_name(self, name: str) -> str:
        """Normalize author name for comparison.

        Args:
            name: Author name

        Returns:
            Normalized author name
        """
        if name in self.author_cache:
            return self.author_cache[name]

        if not name:
            return ""

        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r"\s+", " ", name.lower().strip())

        # Remove common prefixes/suffixes
        prefixes = ["dr.", "prof.", "mr.", "ms.", "mrs."]
        suffixes = ["jr.", "sr.", "iii", "iv", "phd", "md"]

        words = normalized.split()

        # Remove prefixes
        if words and words[0] in prefixes:
            words = words[1:]

        # Remove suffixes
        if words and words[-1] in suffixes:
            words = words[:-1]

        # Handle "Last, First" format
        if len(words) >= 2 and "," in words[0]:
            parts = normalized.split(",")
            if len(parts) == 2:
                last = parts[0].strip()
                first = parts[1].strip()
                normalized = f"{first} {last}"
            else:
                normalized = " ".join(words)
        else:
            normalized = " ".join(words)

        # Remove punctuation except spaces
        normalized = re.sub(r"[^\w\s]", "", normalized)

        self.author_cache[name] = normalized
        return normalized

    def _normalize_institution_name(self, name: str) -> str:
        """Normalize institution name for comparison.

        Args:
            name: Institution name

        Returns:
            Normalized institution name
        """
        if name in self.institution_cache:
            return self.institution_cache[name]

        if not name:
            return ""

        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r"\s+", " ", name.lower().strip())

        # Remove common institution words that don't affect identity
        remove_words = [
            "university",
            "college",
            "institute",
            "school",
            "center",
            "centre",
            "hospital",
            "medical",
            "health",
            "system",
            "dept",
            "department",
            "faculty",
            "division",
            "laboratory",
            "lab",
            "research",
            "sciences",
        ]

        words = normalized.split()
        # Keep core identifying words
        core_words = [word for word in words if word not in remove_words]

        # If removing common words leaves too few words, keep original
        if len(core_words) < 2 and len(words) > 2:
            normalized = " ".join(words)
        else:
            normalized = " ".join(core_words)

        # Remove punctuation except spaces
        normalized = re.sub(r"[^\w\s]", "", normalized)

        self.institution_cache[name] = normalized
        return normalized

    def _are_similar_authors(self, name1: str, name2: str) -> bool:
        """Check if two author names are similar enough to be the same person.

        Args:
            name1: First author name (normalized)
            name2: Second author name (normalized)

        Returns:
            True if names are similar enough
        """
        if not name1 or not name2:
            return False

        # Exact match
        if name1 == name2:
            return True

        # Check for initials vs full names
        words1 = name1.split()
        words2 = name2.split()

        # Handle case where one name has initials
        if self._names_match_with_initials(words1, words2):
            return True

        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, name1, name2).ratio()
        return similarity >= self.author_threshold

    def _names_match_with_initials(self, words1: List[str], words2: List[str]) -> bool:
        """Check if names match allowing for initials.

        Args:
            words1: First name as list of words
            words2: Second name as list of words

        Returns:
            True if names match with initials
        """
        if len(words1) != len(words2):
            return False

        for w1, w2 in zip(words1, words2):
            # If one is initial and other is full word
            if len(w1) == 1 and len(w2) > 1:
                if not w2.startswith(w1):
                    return False
            elif len(w2) == 1 and len(w1) > 1:
                if not w1.startswith(w2):
                    return False
            elif w1 != w2:
                return False

        return True

    def _are_similar_institutions(self, name1: str, name2: str) -> bool:
        """Check if two institution names are similar enough to be the same.

        Args:
            name1: First institution name (normalized)
            name2: Second institution name (normalized)

        Returns:
            True if institutions are similar enough
        """
        if not name1 or not name2:
            return False

        # Exact match
        if name1 == name2:
            return True

        # Use sequence matcher for fuzzy matching
        similarity = SequenceMatcher(None, name1, name2).ratio()
        return similarity >= self.institution_threshold

    def analyze_citation_patterns(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Analyze citation patterns across the paper collection.

        Args:
            papers: List of paper records

        Returns:
            Dictionary with citation pattern analysis
        """
        if not papers:
            return {}

        total_citations = sum(paper.citation_count or 0 for paper in papers)
        total_independent = sum(paper.independent_citations or 0 for paper in papers)
        total_self = sum(paper.self_citations or 0 for paper in papers)

        # Field-wise analysis
        field_patterns = defaultdict(
            lambda: {"papers": 0, "citations": 0, "independent": 0, "self": 0}
        )

        for paper in papers:
            field = paper.primary_field or "Unknown"
            field_patterns[field]["papers"] += 1
            field_patterns[field]["citations"] += paper.citation_count or 0
            field_patterns[field]["independent"] += paper.independent_citations or 0
            field_patterns[field]["self"] += paper.self_citations or 0

        # Calculate ratios by field
        for field, stats in field_patterns.items():
            if stats["citations"] > 0:
                stats["independence_ratio"] = stats["independent"] / stats["citations"]
                stats["self_citation_ratio"] = stats["self"] / stats["citations"]
            else:
                stats["independence_ratio"] = 0.0
                stats["self_citation_ratio"] = 0.0

        # Year-wise analysis
        year_patterns = defaultdict(
            lambda: {"papers": 0, "citations": 0, "independent": 0, "self": 0}
        )

        for paper in papers:
            year = paper.year or 0
            if year > 0:
                year_patterns[year]["papers"] += 1
                year_patterns[year]["citations"] += paper.citation_count or 0
                year_patterns[year]["independent"] += paper.independent_citations or 0
                year_patterns[year]["self"] += paper.self_citations or 0

        analysis = {
            "total_papers": len(papers),
            "total_citations": total_citations,
            "total_independent_citations": total_independent,
            "total_self_citations": total_self,
            "overall_independence_ratio": total_independent / total_citations
            if total_citations > 0
            else 0.0,
            "overall_self_citation_ratio": total_self / total_citations
            if total_citations > 0
            else 0.0,
            "field_patterns": dict(field_patterns),
            "year_patterns": dict(year_patterns),
            "highly_independent_papers": [
                paper.id
                for paper in papers
                if paper.citation_count
                and paper.citation_count > 5
                and paper.independent_citations
                and paper.independent_citations / paper.citation_count > 0.8
            ],
            "high_self_citation_papers": [
                paper.id
                for paper in papers
                if paper.citation_count
                and paper.citation_count > 5
                and paper.self_citations
                and paper.self_citations / paper.citation_count > 0.5
            ],
        }

        return analysis

    def generate_independence_report(self, papers: List[PaperRecord]) -> Dict[str, Any]:
        """Generate comprehensive independence analysis report.

        Args:
            papers: List of paper records

        Returns:
            Detailed independence report
        """
        citation_patterns = self.analyze_citation_patterns(papers)

        # Quality metrics
        papers_with_high_independence = sum(
            1
            for paper in papers
            if paper.citation_count
            and paper.citation_count > 0
            and paper.independent_citations
            and paper.independent_citations / paper.citation_count > 0.7
        )

        papers_with_citations = sum(
            1 for paper in papers if paper.citation_count and paper.citation_count > 0
        )

        independence_quality_score = (
            papers_with_high_independence / papers_with_citations * 100
            if papers_with_citations > 0
            else 0
        )

        report = {
            "summary": citation_patterns,
            "quality_metrics": {
                "independence_quality_score": independence_quality_score,
                "papers_with_high_independence": papers_with_high_independence,
                "papers_with_citations": papers_with_citations,
                "average_independence_ratio": np.mean(
                    [
                        paper.independent_citations / paper.citation_count
                        for paper in papers
                        if paper.citation_count
                        and paper.citation_count > 0
                        and paper.independent_citations is not None
                    ]
                )
                if papers
                else 0.0,
            },
            "recommendations": self._generate_independence_recommendations(papers),
            "top_independent_papers": sorted(
                [
                    {
                        "id": paper.id,
                        "title": paper.title,
                        "citation_count": paper.citation_count,
                        "independent_citations": paper.independent_citations,
                        "independence_ratio": paper.independent_citations
                        / paper.citation_count
                        if paper.citation_count
                        else 0,
                    }
                    for paper in papers
                    if paper.citation_count
                    and paper.citation_count > 5
                    and paper.independent_citations
                ],
                key=lambda x: x["independence_ratio"],
                reverse=True,
            )[:10],
        }

        return report

    def _generate_independence_recommendations(
        self, papers: List[PaperRecord]
    ) -> List[str]:
        """Generate recommendations for improving independence metrics.

        Args:
            papers: List of paper records

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not papers:
            return recommendations

        total_papers = len(papers)
        papers_with_citations = [
            p for p in papers if p.citation_count and p.citation_count > 0
        ]

        if not papers_with_citations:
            recommendations.append(
                "Focus on publishing work that attracts independent citations."
            )
            return recommendations

        # Calculate overall metrics
        total_citations = sum(p.citation_count for p in papers_with_citations)
        total_independent = sum(
            p.independent_citations or 0 for p in papers_with_citations
        )
        independence_ratio = (
            total_independent / total_citations if total_citations > 0 else 0
        )

        if independence_ratio < 0.5:
            recommendations.append(
                f"Independence ratio is {independence_ratio:.1%}. Consider highlighting broader impact "
                "and practical applications to attract more independent citations."
            )

        if independence_ratio > 0.8:
            recommendations.append(
                f"Excellent independence ratio of {independence_ratio:.1%}. This demonstrates "
                "strong independent recognition of your work."
            )

        # Field-specific recommendations
        field_patterns = defaultdict(list)
        for paper in papers_with_citations:
            field = paper.primary_field or "Unknown"
            if paper.independent_citations is not None and paper.citation_count:
                ratio = paper.independent_citations / paper.citation_count
                field_patterns[field].append(ratio)

        for field, ratios in field_patterns.items():
            if len(ratios) >= 3:  # Need enough papers for meaningful analysis
                avg_ratio = np.mean(ratios)
                if avg_ratio < 0.6:
                    recommendations.append(
                        f"In {field}, consider collaborative work with researchers from "
                        "different institutions to increase independent citations."
                    )

        return recommendations
