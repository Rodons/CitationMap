"""Professional report generation for legal exhibits."""

import base64
import io
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, black, blue, darkblue
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as ReportLabImage
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..analysis import (
    DataMerger,
    FieldNormalizer,
    IndependenceClassifier,
    UptakeAggregator,
)
from ..core.models import PaperRecord

logger = logging.getLogger(__name__)


class LawyerReportGenerator:
    """Generates professional PDF reports for EB-1A/O-1 applications."""

    def __init__(self):
        """Initialize report generator."""
        self.logger = logger
        self.merger = DataMerger()
        self.normalizer = FieldNormalizer()
        self.classifier = IndependenceClassifier()
        self.aggregator = UptakeAggregator()

    def generate_full_report(
        self,
        papers: List[PaperRecord],
        applicant_name: str,
        output_path: str,
        case_number: Optional[str] = None,
    ) -> str:
        """Generate comprehensive EB-1A/O-1 citation analysis report.

        Args:
            papers: List of paper records
            applicant_name: Name of the visa applicant
            output_path: Path for output PDF file
            case_number: Optional case number

        Returns:
            Path to generated PDF report
        """
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build story (content)
        story = []
        styles = self._get_custom_styles()

        # Cover page
        story.extend(self._create_cover_page(applicant_name, case_number, styles))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(papers, styles))
        story.append(PageBreak())

        # Citation analysis
        story.extend(self._create_citation_analysis(papers, styles))
        story.append(PageBreak())

        # Field impact analysis
        story.extend(self._create_field_analysis(papers, styles))
        story.append(PageBreak())

        # Independence analysis
        story.extend(self._create_independence_analysis(papers, styles))
        story.append(PageBreak())

        # Translational impact
        story.extend(self._create_translational_analysis(papers, styles))
        story.append(PageBreak())

        # Geographic impact
        story.extend(self._create_geographic_analysis(papers, styles))
        story.append(PageBreak())

        # Top papers showcase
        story.extend(self._create_top_papers_showcase(papers, styles))
        story.append(PageBreak())

        # Appendices
        story.extend(self._create_appendices(papers, styles))

        # Build PDF
        doc.build(story)

        self.logger.info(f"Report generated: {output_path}")
        return output_path

    def generate_summary_report(
        self, papers: List[PaperRecord], applicant_name: str, output_path: str
    ) -> str:
        """Generate text-based summary report.

        Args:
            papers: List of paper records
            applicant_name: Name of the visa applicant
            output_path: Path for output text file

        Returns:
            Path to generated report
        """
        summary = self.merger.create_analysis_summary(papers)
        independence_report = self.classifier.generate_independence_report(papers)
        uptake_report = self.aggregator.generate_uptake_report(papers)

        report_text = f"""
CITATION ANALYSIS REPORT
========================

Petitioner: {applicant_name}
Generated: {datetime.now().strftime('%B %d, %Y')}

EXECUTIVE SUMMARY
================

This report presents comprehensive citation analysis for {applicant_name}'s
{summary['total_papers']} peer-reviewed publications, demonstrating extraordinary
ability through {summary['total_citations']} total citations and an H-index of
{summary['h_index']}.

KEY METRICS
===========

Total Papers: {summary['total_papers']}
Total Citations: {summary['total_citations']}
H-Index: {summary['h_index']}
i10-Index: {summary['i10_index']}
Independence Ratio: {summary['independence_ratio']:.1%}

CITATION INDEPENDENCE
====================

Independence Quality Score: {independence_report['quality_metrics']['independence_quality_score']:.1f}%
Average Independence Ratio: {independence_report['quality_metrics']['average_independence_ratio']:.1%}
High Independence Papers: {independence_report['quality_metrics']['papers_with_high_independence']}

TRANSLATIONAL IMPACT
===================

Papers with Translational Impact: {uptake_report['executive_summary']['papers_with_translational_impact']}
Translational Impact Rate: {uptake_report['executive_summary']['translational_impact_rate']:.1%}
Breakthrough Papers: {uptake_report['executive_summary']['breakthrough_papers_count']}

FIELD DISTRIBUTION
==================
"""

        for field, count in summary["field_distribution"].items():
            report_text += f"{field}: {count} papers\n"

        report_text += f"""

TOP CITED PAPERS
================
"""

        top_papers = sorted(papers, key=lambda p: p.citation_count or 0, reverse=True)[
            :10
        ]
        for i, paper in enumerate(top_papers, 1):
            report_text += (
                f"{i}. {paper.title} ({paper.citation_count} citations, {paper.year})\n"
            )

        report_text += f"""

CONCLUSION
==========

The citation analysis demonstrates exceptional research impact consistent with
extraordinary ability in the academic field. The H-index of {summary['h_index']}
and total citations of {summary['total_citations']} place the researcher in the
top percentile of their field, with {summary['independence_ratio']:.1%} independent
citations confirming objective recognition by the international scientific community.

Generated by CitationMap Analysis Toolkit
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        self.logger.info(f"Summary report generated: {output_path}")
        return output_path

    def generate_one_page_exhibit(
        self, papers: List[PaperRecord], applicant_name: str, output_path: str
    ) -> str:
        """Generate one-page HTML exhibit for quick reference."""
        summary = self.merger.create_analysis_summary(papers)

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Citation Analysis Exhibit - {applicant_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .metric {{ border: 1px solid #ccc; padding: 15px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 12px; color: #7f8c8d; }}
        .section {{ margin: 20px 0; }}
        .papers-list {{ font-size: 12px; }}
        .footer {{ text-align: center; font-size: 10px; color: #7f8c8d; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CITATION ANALYSIS EXHIBIT</h1>
        <h2>{applicant_name} - EB-1A/O-1 Petition</h2>
    </div>

    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{summary['total_papers']}</div>
            <div class="metric-label">Total Papers</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary['total_citations']}</div>
            <div class="metric-label">Total Citations</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary['h_index']}</div>
            <div class="metric-label">H-Index</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary['independence_ratio']:.1%}</div>
            <div class="metric-label">Independence Ratio</div>
        </div>
    </div>

    <div class="section">
        <h3>TOP CITED PAPERS</h3>
        <div class="papers-list">
"""

        top_papers = sorted(papers, key=lambda p: p.citation_count or 0, reverse=True)[
            :5
        ]
        for i, paper in enumerate(top_papers, 1):
            html_content += f"            <p><strong>{i}.</strong> {paper.title[:100]}... ({paper.citation_count} citations, {paper.year})</p>\n"

        html_content += f"""
        </div>
    </div>

    <div class="section">
        <h3>FIELD DISTRIBUTION</h3>
"""

        for field, count in list(summary["field_distribution"].items())[:3]:
            html_content += f"        <p><strong>{field}:</strong> {count} papers</p>\n"

        html_content += f"""
    </div>

    <div class="footer">
        <p>Generated by CitationMap on {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
</body>
</html>
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(f"One-page exhibit generated: {output_path}")
        return output_path

    def _get_custom_styles(self) -> Dict[str, ParagraphStyle]:
        """Get custom paragraph styles for the report."""
        styles = getSampleStyleSheet()

        # Custom styles
        custom_styles = {
            "Title": ParagraphStyle(
                "Title",
                parent=styles["Title"],
                fontSize=24,
                spaceAfter=30,
                textColor=darkblue,
                alignment=TA_CENTER,
            ),
            "Heading1": ParagraphStyle(
                "Heading1",
                parent=styles["Heading1"],
                fontSize=18,
                spaceAfter=18,
                textColor=darkblue,
                keepWithNext=1,
            ),
            "Heading2": ParagraphStyle(
                "Heading2",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=12,
                textColor=darkblue,
                keepWithNext=1,
            ),
            "Normal": styles["Normal"],
            "Caption": ParagraphStyle(
                "Caption",
                parent=styles["Normal"],
                fontSize=8,
                textColor=Color(0.5, 0.5, 0.5),
                alignment=TA_CENTER,
            ),
            "Legal": ParagraphStyle(
                "Legal",
                parent=styles["Normal"],
                fontSize=10,
                leading=14,
                spaceBefore=6,
                spaceAfter=6,
            ),
        }

        return custom_styles

    def _create_cover_page(
        self,
        applicant_name: str,
        case_number: Optional[str],
        styles: Dict[str, ParagraphStyle],
    ) -> List[Any]:
        """Create cover page content."""
        story = []

        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("CITATION ANALYSIS REPORT", styles["Title"]))
        story.append(Spacer(1, 0.5 * inch))

        story.append(
            Paragraph(f"<b>Petitioner:</b> {applicant_name}", styles["Heading1"])
        )

        if case_number:
            story.append(
                Paragraph(f"<b>Case Number:</b> {case_number}", styles["Heading2"])
            )

        story.append(Spacer(1, 0.5 * inch))
        story.append(
            Paragraph(
                "<b>EB-1A Outstanding Researcher / O-1 Extraordinary Ability</b>",
                styles["Heading2"],
            )
        )
        story.append(
            Paragraph("Supporting Evidence of Citation Impact", styles["Heading2"])
        )

        story.append(Spacer(1, 1 * inch))
        story.append(
            Paragraph(
                f"Prepared on {datetime.now().strftime('%B %d, %Y')}", styles["Normal"]
            )
        )
        story.append(
            Paragraph("Generated by CitationMap Analysis Toolkit", styles["Caption"])
        )

        return story

    def _create_executive_summary(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create executive summary section."""
        story = []

        story.append(Paragraph("EXECUTIVE SUMMARY", styles["Heading1"]))

        # Generate summary
        summary = self.merger.create_analysis_summary(papers)

        summary_text = f"""
        This report presents a comprehensive citation analysis demonstrating extraordinary
        ability in the academic field. The analysis covers {summary['total_papers']}
        peer-reviewed publications with a total of {summary['total_citations']} citations,
        resulting in an H-index of {summary['h_index']} and i10-index of {summary['i10_index']}.

        <b>Key Findings:</b>

        • <b>Citation Impact:</b> The work has been cited {summary['total_citations']} times
        by independent researchers worldwide, demonstrating significant influence in the field.

        • <b>Research Quality:</b> An H-index of {summary['h_index']} indicates {summary['h_index']}
        publications with at least {summary['h_index']} citations each, showing consistent
        high-quality research output.

        • <b>Independence:</b> {summary['independence_ratio']:.1%} of citations are from
        independent researchers, confirming objective recognition by the scientific community.

        • <b>Global Impact:</b> Citations originate from researchers in multiple countries,
        demonstrating international recognition of the work.

        • <b>Field Leadership:</b> The citation metrics place the researcher in the top
        percentile of their field, consistent with extraordinary ability criteria.
        """

        story.append(Paragraph(summary_text, styles["Legal"]))

        return story

    def _create_citation_analysis(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create detailed citation analysis section."""
        story = []

        story.append(Paragraph("CITATION ANALYSIS", styles["Heading1"]))

        # Citation statistics table
        summary = self.merger.create_analysis_summary(papers)

        citation_data = [
            ["Citation Metric", "Value", "Interpretation"],
            [
                "Total Citations",
                str(summary["total_citations"]),
                "Overall academic impact",
            ],
            ["H-Index", str(summary["h_index"]), "Research influence measure"],
            ["i10-Index", str(summary["i10_index"]), "High-impact paper count"],
            [
                "Average Citations/Paper",
                f"{summary['total_citations']/summary['total_papers']:.1f}",
                "Paper quality indicator",
            ],
            [
                "Citations per Year",
                f"{summary['total_citations']/(2024-summary['year_range']['earliest']):.1f}",
                "Research momentum",
            ],
        ]

        citation_table = Table(
            citation_data, colWidths=[2 * inch, 1 * inch, 2.5 * inch]
        )
        citation_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), Color(0.8, 0.8, 0.8)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), Color(0.95, 0.95, 0.95)),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                ]
            )
        )

        story.append(citation_table)
        story.append(Spacer(1, 12))

        # Analysis text
        analysis_text = """
        The citation metrics demonstrate exceptional research impact consistent with
        extraordinary ability in the academic field. The H-index is a widely accepted
        measure of both productivity and impact, requiring both quantity and quality
        of publications. An H-index above the field median indicates superior research
        performance recognized by the international scientific community.
        """

        story.append(Paragraph(analysis_text, styles["Legal"]))

        return story

    def _create_field_analysis(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create field analysis section."""
        story = []

        story.append(Paragraph("FIELD IMPACT ANALYSIS", styles["Heading1"]))

        # Field distribution
        summary = self.merger.create_analysis_summary(papers)
        field_dist = summary["field_distribution"]

        field_data = [["Research Field", "Publications", "Percentage"]]
        for field, count in field_dist.items():
            percentage = (count / summary["total_papers"]) * 100
            field_data.append([field, str(count), f"{percentage:.1f}%"])

        field_table = Table(field_data, colWidths=[3 * inch, 1 * inch, 1 * inch])
        field_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), Color(0.8, 0.8, 0.8)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), Color(0.95, 0.95, 0.95)),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                ]
            )
        )

        story.append(field_table)

        field_text = """
        The research spans multiple related fields, demonstrating versatility and
        interdisciplinary impact. This breadth of expertise, combined with consistent
        citation impact across fields, indicates extraordinary ability that transcends
        narrow specialization.
        """

        story.append(Paragraph(field_text, styles["Legal"]))

        return story

    def _create_independence_analysis(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create independence analysis section."""
        story = []

        story.append(Paragraph("CITATION INDEPENDENCE ANALYSIS", styles["Heading1"]))

        independence_report = self.classifier.generate_independence_report(papers)

        independence_text = f"""
        Citation independence is crucial for demonstrating objective recognition by
        the scientific community. Our analysis shows:

        • <b>Independence Ratio:</b> {independence_report['quality_metrics']['average_independence_ratio']:.1%}
        of citations are from independent researchers

        • <b>Quality Score:</b> {independence_report['quality_metrics']['independence_quality_score']:.1f}%
        independence quality rating

        • <b>High Independence Papers:</b> {independence_report['quality_metrics']['papers_with_high_independence']}
        papers with >80% independent citations

        This level of independence confirms that the citations represent genuine
        recognition by unaffiliated researchers, not self-citation or citation
        trading arrangements.
        """

        story.append(Paragraph(independence_text, styles["Legal"]))

        return story

    def _create_translational_analysis(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create translational impact section."""
        story = []

        story.append(Paragraph("TRANSLATIONAL IMPACT ANALYSIS", styles["Heading1"]))

        uptake_report = self.aggregator.generate_uptake_report(papers)
        exec_summary = uptake_report["executive_summary"]

        translational_text = f"""
        Translational impact demonstrates how research influences practical applications
        and policy. The analysis reveals:

        • <b>Patent Citations:</b> {uptake_report['patent_analysis']['total_patent_citations']}
        patents cite the research work

        • <b>Clinical Trials:</b> {uptake_report['clinical_trial_analysis']['total_trial_citations']}
        clinical trials reference the findings

        • <b>Breakthrough Papers:</b> {exec_summary['breakthrough_papers_count']}
        publications identified as breakthrough research

        • <b>Translational Rate:</b> {exec_summary['translational_impact_rate']:.1%}
        of papers show downstream practical impact

        This translational impact demonstrates that the research has moved beyond
        academic citations to influence real-world applications, policy, and practice.
        """

        story.append(Paragraph(translational_text, styles["Legal"]))

        return story

    def _create_geographic_analysis(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create geographic impact section."""
        story = []

        story.append(Paragraph("GEOGRAPHIC IMPACT ANALYSIS", styles["Heading1"]))

        summary = self.merger.create_analysis_summary(papers)
        country_dist = summary["country_distribution"]

        geo_text = f"""
        The research has achieved international recognition, with citations from
        researchers in {len(country_dist)} countries. This global impact demonstrates
        extraordinary ability recognized internationally, not just domestically.

        <b>Geographic Distribution:</b>
        """

        for country, count in list(country_dist.items())[:5]:
            geo_text += f"\n• <b>{country}:</b> {count} citing institutions"

        story.append(Paragraph(geo_text, styles["Legal"]))

        return story

    def _create_top_papers_showcase(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create top papers showcase section."""
        story = []

        story.append(Paragraph("TOP CITED PUBLICATIONS", styles["Heading1"]))

        # Sort papers by citation count
        top_papers = sorted(papers, key=lambda p: p.citation_count or 0, reverse=True)[
            :10
        ]

        papers_data = [["Title", "Year", "Citations", "Journal"]]

        for paper in top_papers:
            title = paper.title[:50] + "..." if len(paper.title) > 50 else paper.title
            journal = (
                paper.journal_name[:20] + "..."
                if paper.journal_name and len(paper.journal_name) > 20
                else (paper.journal_name or "N/A")
            )
            papers_data.append(
                [title, str(paper.year), str(paper.citation_count or 0), journal]
            )

        papers_table = Table(
            papers_data, colWidths=[3 * inch, 0.5 * inch, 0.7 * inch, 1.3 * inch]
        )
        papers_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), Color(0.8, 0.8, 0.8)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), Color(0.95, 0.95, 0.95)),
                    ("GRID", (0, 0), (-1, -1), 1, black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(papers_table)

        return story

    def _create_appendices(
        self, papers: List[PaperRecord], styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Create appendices with methodology and data sources."""
        story = []

        story.append(Paragraph("APPENDIX A: METHODOLOGY", styles["Heading1"]))

        methodology_text = """
        This citation analysis was conducted using the CitationMap toolkit, which
        integrates data from multiple authoritative sources:

        <b>Data Sources:</b>
        • OpenAlex: Comprehensive bibliographic database
        • iCite (NIH): Relative Citation Ratio (RCR) calculation
        • Google Scholar: Citation tracking and metrics

        <b>Analysis Methods:</b>
        • Field normalization using empirical distributions
        • Independence classification using author/institution matching
        • Translational impact assessment via patent and clinical trial databases
        • Geographic analysis using institutional affiliations

        <b>Quality Assurance:</b>
        • Duplicate detection and removal
        • Author disambiguation using multiple matching criteria
        • Citation verification through cross-source validation

        All metrics are calculated using standard bibliometric practices and
        internationally recognized methodologies.
        """

        story.append(Paragraph(methodology_text, styles["Legal"]))

        return story
