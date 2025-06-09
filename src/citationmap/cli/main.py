"""Main CLI application for CitationMap."""

import logging
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..analysis import DataMerger, IndependenceClassifier, UptakeAggregator
from ..core.models import PaperRecord
from ..data_acquisition import OpenAlexClient, iCiteClient
from ..visualization import ChartGenerator, CitationMapFactory, LawyerReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(
    name="citationmap",
    help="CitationMap: Comprehensive citation analysis for EB-1A/O-1 visa applications",
)

console = Console()


@app.command()
def analyze(
    orcid_id: str = typer.Argument(..., help="ORCID ID of the researcher"),
    output_dir: Path = typer.Option(
        Path("./citation_analysis"),
        "--output",
        "-o",
        help="Output directory for analysis results",
    ),
    applicant_name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Name of visa applicant for reports"
    ),
):
    """Run comprehensive citation analysis for an ORCID ID."""

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel.fit(
            f"CitationMap Analysis\n" f"ORCID: {orcid_id}\n" f"Output: {output_dir}"
        )
    )

    try:
        # Step 1: Data acquisition
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Fetch papers
            fetch_task = progress.add_task("Fetching publication data...", total=None)
            papers = _fetch_papers(orcid_id)
            progress.update(fetch_task, description=f"Found {len(papers)} papers")

            if not papers:
                console.print("[red]No papers found for ORCID ID[/red]")
                raise typer.Exit(1)

            # Analysis
            analysis_task = progress.add_task(
                "Running citation analysis...", total=None
            )
            analysis_results = _run_analysis(papers)
            progress.update(analysis_task, description="Analysis complete")

            # Reports
            report_task = progress.add_task("Generating reports...", total=None)
            _generate_reports(papers, output_dir, applicant_name or "Applicant")
            progress.update(report_task, description="Reports generated")

        # Display summary
        _display_summary(papers, analysis_results)

        console.print(
            f"\n[green]✓ Analysis complete! Results saved to {output_dir}[/green]"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats(orcid_id: str = typer.Argument(..., help="ORCID ID of the researcher")):
    """Display citation statistics summary."""
    try:
        # Fetch papers
        with console.status("Loading data..."):
            papers = _fetch_papers(orcid_id)

        if not papers:
            console.print("[red]No papers found for ORCID ID[/red]")
            raise typer.Exit(1)

        # Run analysis
        analysis_results = _run_analysis(papers)

        # Display results
        _display_summary(papers, analysis_results)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _fetch_papers(orcid_id: str) -> List[PaperRecord]:
    """Fetch papers for ORCID ID."""
    openalex = OpenAlexClient()
    papers = openalex.fetch_papers_by_orcid(orcid_id)

    # Enhance with iCite data
    icite = iCiteClient()
    for paper in papers:
        if paper.pmid:
            icite_data = icite.fetch_paper_metrics(paper.pmid)
            if icite_data:
                paper.rcr = icite_data.get("relative_citation_ratio")

    return papers


def _run_analysis(papers: List[PaperRecord]) -> dict:
    """Run comprehensive analysis."""
    merger = DataMerger()
    classifier = IndependenceClassifier()
    aggregator = UptakeAggregator()

    # Create summary
    summary = merger.create_analysis_summary(papers)

    # Independence analysis
    independence_report = classifier.generate_independence_report(papers)

    # Translational impact
    uptake_report = aggregator.generate_uptake_report(papers)

    return {
        "summary": summary,
        "independence": independence_report,
        "uptake": uptake_report,
    }


def _generate_reports(papers: List[PaperRecord], output_dir: Path, applicant_name: str):
    """Generate reports."""
    report_generator = LawyerReportGenerator()

    # HTML exhibit
    report_generator.generate_one_page_exhibit(
        papers, applicant_name, str(output_dir / "exhibit.html")
    )

    # Text report
    report_generator.generate_summary_report(
        papers, applicant_name, str(output_dir / "summary_report.txt")
    )

    # Charts
    chart_generator = ChartGenerator()

    timeline_fig = chart_generator.create_citation_timeline(papers)
    chart_generator.export_chart(
        timeline_fig, str(output_dir / "citation_timeline.html")
    )

    field_fig = chart_generator.create_field_comparison_chart(papers)
    chart_generator.export_chart(field_fig, str(output_dir / "field_comparison.html"))


def _display_summary(papers: List[PaperRecord], analysis_results: dict):
    """Display analysis summary in console."""
    summary = analysis_results["summary"]

    # Main metrics table
    table = Table(title="Citation Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Papers", str(summary["total_papers"]))
    table.add_row("Total Citations", str(summary["total_citations"]))
    table.add_row("H-Index", str(summary["h_index"]))
    table.add_row("i10-Index", str(summary["i10_index"]))
    table.add_row("Independence Ratio", f"{summary['independence_ratio']:.1%}")

    console.print(table)

    # Top papers
    if papers:
        top_papers = sorted(papers, key=lambda p: p.citation_count or 0, reverse=True)[
            :3
        ]
        console.print("\n[bold]Top Cited Papers:[/bold]")
        for i, paper in enumerate(top_papers, 1):
            console.print(f"{i}. {paper.title} ({paper.citation_count or 0} citations)")


if __name__ == "__main__":
    app()
