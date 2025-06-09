#!/usr/bin/env python3
"""
Phase 3 Demo: Visualization & Reporting

This script demonstrates the visualization and reporting capabilities
of CitationMap for EB-1A/O-1 visa applications.
"""

import logging
from datetime import datetime
from pathlib import Path

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import CitationMap modules
from citationmap.core.models import (
    Author,
    Citation,
    FieldOfStudy,
    Institution,
    PaperRecord,
)
from citationmap.visualization import (
    ChartGenerator,
    CitationMapFactory,
    LawyerReportGenerator,
)


def create_sample_papers():
    """Create sample papers for demonstration."""
    papers = []

    # Sample institutions
    mit = Institution(
        display_name="Massachusetts Institute of Technology",
        country_code="US",
        latitude=42.3601,
        longitude=-71.0942,
    )

    stanford = Institution(
        display_name="Stanford University",
        country_code="US",
        latitude=37.4275,
        longitude=-122.1697,
    )

    oxford = Institution(
        display_name="University of Oxford",
        country_code="GB",
        latitude=51.7520,
        longitude=-1.2577,
    )

    # Sample authors
    author1 = Author(
        display_name="Dr. Jane Smith", institutions=[mit], orcid="0000-0001-2345-6789"
    )

    author2 = Author(
        display_name="Prof. John Doe",
        institutions=[stanford],
        orcid="0000-0002-3456-7890",
    )

    author3 = Author(
        display_name="Dr. Alice Johnson",
        institutions=[oxford],
        orcid="0000-0003-4567-8901",
    )

    # Sample fields
    ai_field = FieldOfStudy(
        id="ai", display_name="Artificial Intelligence", level=1, score=0.95
    )
    ml_field = FieldOfStudy(
        id="ml", display_name="Machine Learning", level=1, score=0.90
    )
    cs_field = FieldOfStudy(
        id="cs", display_name="Computer Science", level=0, score=0.85
    )

    # Sample papers
    papers.append(
        PaperRecord(
            id="paper_1",
            title="Revolutionary Advances in Deep Learning Architecture",
            authors=[author1, author2],
            year=2023,
            journal="Nature Machine Intelligence",
            citation_count=156,
            independent_citations=142,
            rcr=3.2,
            primary_field="Computer Science",
            fields_of_study=[ai_field, ml_field, cs_field],
            citations=[
                Citation(citing_paper_id="cite_1", citing_authors=[author3]),
                Citation(citing_paper_id="cite_2", citing_authors=[author1]),
            ],
        )
    )

    papers.append(
        PaperRecord(
            id="paper_2",
            title="Scalable Machine Learning for Healthcare Applications",
            authors=[author1, author3],
            year=2022,
            journal="Science",
            citation_count=89,
            independent_citations=81,
            rcr=2.8,
            primary_field="Computer Science",
            fields_of_study=[ml_field, ai_field],
            citations=[Citation(citing_paper_id="cite_3", citing_authors=[author2])],
        )
    )

    papers.append(
        PaperRecord(
            id="paper_3",
            title="Ethical AI: Principles and Implementation",
            authors=[author2, author1],
            year=2021,
            journal="ACM Computing Reviews",
            citation_count=45,
            independent_citations=39,
            rcr=1.9,
            primary_field="Computer Science",
            fields_of_study=[ai_field, cs_field],
        )
    )

    return papers


def demo_charts(papers, output_dir):
    """Demonstrate chart generation."""
    logger.info("🎯 Generating interactive charts...")

    chart_generator = ChartGenerator()

    # Citation timeline
    timeline_fig = chart_generator.create_citation_timeline(
        papers, "Sample Citation Timeline"
    )
    chart_generator.export_chart(
        timeline_fig, str(output_dir / "citation_timeline.html")
    )
    logger.info("✓ Citation timeline chart created")

    # Field comparison
    field_fig = chart_generator.create_field_comparison_chart(
        papers, "Impact by Research Field"
    )
    chart_generator.export_chart(field_fig, str(output_dir / "field_comparison.html"))
    logger.info("✓ Field comparison chart created")

    # RCR distribution
    rcr_fig = chart_generator.create_rcr_distribution_chart(
        papers, "RCR Distribution Analysis"
    )
    chart_generator.export_chart(rcr_fig, str(output_dir / "rcr_distribution.html"))
    logger.info("✓ RCR distribution chart created")


def demo_maps(papers, output_dir):
    """Demonstrate map generation."""
    logger.info("🗺️ Generating geographic citation maps...")

    map_factory = CitationMapFactory()

    # Global citation map
    citation_map = map_factory.create_global_citation_map(papers)
    map_factory.export_map_html(
        citation_map, str(output_dir / "global_citation_map.html")
    )
    logger.info("✓ Global citation map created")


def demo_reports(papers, output_dir):
    """Demonstrate report generation."""
    logger.info("📄 Generating lawyer-ready reports...")

    report_generator = LawyerReportGenerator()

    # HTML exhibit
    report_generator.generate_one_page_exhibit(
        papers, "Dr. Jane Smith", str(output_dir / "visa_exhibit.html")
    )
    logger.info("✓ HTML exhibit created")

    # Text summary
    report_generator.generate_summary_report(
        papers, "Dr. Jane Smith", str(output_dir / "summary_report.txt")
    )
    logger.info("✓ Text summary report created")


def main():
    """Run Phase 3 demonstration."""
    print("🚀 CitationMap Phase 3 Demo: Visualization & Reporting\n")

    # Setup output directory
    output_dir = Path("./phase3_demo_output")
    output_dir.mkdir(exist_ok=True)

    # Create sample data
    logger.info("📚 Creating sample publication data...")
    papers = create_sample_papers()
    logger.info(f"✓ Created {len(papers)} sample papers")

    # Run demonstrations
    try:
        demo_charts(papers, output_dir)
        demo_maps(papers, output_dir)
        demo_reports(papers, output_dir)

        print(f"\n🎉 Demo complete! Check outputs in: {output_dir.absolute()}")
        print("\nGenerated files:")
        for file in output_dir.glob("*"):
            print(f"  • {file.name}")

        print("\n📋 Quick Summary:")
        print(f"  • Total Papers: {len(papers)}")
        print(f"  • Total Citations: {sum(p.citation_count or 0 for p in papers)}")
        print(f"  • Average RCR: {sum(p.rcr or 0 for p in papers) / len(papers):.1f}")

        # Calculate H-index
        citations = sorted([p.citation_count or 0 for p in papers], reverse=True)
        h_index = 0
        for i, cite_count in enumerate(citations, 1):
            if cite_count >= i:
                h_index = i
            else:
                break
        print(f"  • H-Index: {h_index}")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    main()
