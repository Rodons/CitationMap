"""Streamlit dashboard for interactive citation analysis."""

import logging
from typing import List, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..core.models import PaperRecord
from ..analysis import DataMerger, IndependenceClassifier, UptakeAggregator, FieldNormalizer
from .charts import ChartGenerator
from .maps import CitationMapFactory
from .reports import LawyerReportGenerator

logger = logging.getLogger(__name__)


class StreamlitDashboard:
    """Interactive Streamlit dashboard for citation analysis."""
    
    def __init__(self):
        """Initialize dashboard."""
        self.logger = logger
        self.merger = DataMerger()
        self.classifier = IndependenceClassifier()
        self.aggregator = UptakeAggregator()
        self.normalizer = FieldNormalizer()
        self.chart_generator = ChartGenerator()
        self.map_factory = CitationMapFactory()
        self.report_generator = LawyerReportGenerator()
    
    def run_dashboard(self, papers: List[PaperRecord], applicant_name: str = "Researcher"):
        """Run the main dashboard application."""
        st.set_page_config(
            page_title="CitationMap Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Sidebar
        with st.sidebar:
            st.title("CitationMap")
            st.markdown("**EB-1A/O-1 Citation Analysis**")
            
            # Navigation
            page = st.radio(
                "Navigate to:",
                ["📊 Overview", "📈 Analytics", "🗺️ Geographic Impact", 
                 "🔬 Field Analysis", "📋 Reports", "🔍 Paper Explorer"]
            )
        
        # Main content
        if not papers:
            st.error("No papers loaded. Please provide paper data to begin analysis.")
            return
        
        if page == "📊 Overview":
            self._render_overview_page(papers, applicant_name)
        elif page == "📈 Analytics":
            self._render_analytics_page(papers)
        elif page == "🗺️ Geographic Impact":
            self._render_geographic_page(papers)
        elif page == "🔬 Field Analysis":
            self._render_field_analysis_page(papers)
        elif page == "📋 Reports":
            self._render_reports_page(papers, applicant_name)
        elif page == "🔍 Paper Explorer":
            self._render_paper_explorer_page(papers)
    
    def _render_overview_page(self, papers: List[PaperRecord], applicant_name: str):
        """Render overview page with key metrics."""
        st.title(f"📊 Citation Analysis for {applicant_name}")
        st.markdown("**Comprehensive Citation Analysis for EB-1A/O-1 Visa Applications**")
        
        # Generate analysis
        summary = self.merger.create_analysis_summary(papers)
        independence_report = self.classifier.generate_independence_report(papers)
        uptake_report = self.aggregator.generate_uptake_report(papers)
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Papers", summary['total_papers'])
        with col2:
            st.metric("Total Citations", summary['total_citations'])
        with col3:
            st.metric("H-Index", summary['h_index'])
        with col4:
            st.metric("Independence Ratio", f"{summary['independence_ratio']:.1%}")
        
        # Visual summaries
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Citation Timeline")
            timeline_fig = self.chart_generator.create_citation_timeline(papers)
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        with col2:
            st.subheader("Field Distribution")
            if summary.get('field_distribution'):
                field_df = pd.DataFrame(list(summary['field_distribution'].items()), 
                                      columns=['Field', 'Papers'])
                fig = px.pie(field_df, values='Papers', names='Field', title='Papers by Field')
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_analytics_page(self, papers: List[PaperRecord]):
        """Render detailed analytics page."""
        st.title("📈 Detailed Citation Analytics")
        
        # Filters
        st.subheader("Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_year = min(p.year for p in papers if p.year) if papers else 2000
            max_year = max(p.year for p in papers if p.year) if papers else 2024
            year_range = st.slider("Year Range", min_year, max_year, (min_year, max_year))
        
        with col2:
            min_citations = st.number_input("Min Citations", min_value=0, value=0)
        
        # Filter papers
        filtered_papers = [
            p for p in papers 
            if (p.year and year_range[0] <= p.year <= year_range[1]) and
               (p.citation_count or 0) >= min_citations
        ]
        
        st.markdown(f"**Showing {len(filtered_papers)} papers (filtered from {len(papers)} total)**")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Citation vs Year")
            if filtered_papers:
                df = pd.DataFrame([
                    {'Year': p.year, 'Citations': p.citation_count or 0, 'Title': p.title[:50] + '...'}
                    for p in filtered_papers if p.year
                ])
                fig = px.scatter(df, x='Year', y='Citations', hover_data=['Title'],
                               title='Citation Count by Publication Year')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("RCR Distribution")
            rcr_data = [p.rcr for p in filtered_papers if p.rcr]
            if rcr_data:
                fig = px.histogram(x=rcr_data, title='Relative Citation Ratio Distribution')
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_geographic_page(self, papers: List[PaperRecord]):
        """Render geographic impact page."""
        st.title("🗺️ Geographic Impact Analysis")
        st.markdown("Analysis of collaborative networks and international impact")
        
        # Create geographic visualization
        map_fig = self.map_factory.create_collaboration_map(papers)
        st.plotly_chart(map_fig, use_container_width=True)
    
    def _render_field_analysis_page(self, papers: List[PaperRecord]):
        """Render field analysis page."""
        st.title("🔬 Field Analysis")
        st.markdown("Research field normalization and impact analysis")
        
        # Field comparison chart
        field_fig = self.chart_generator.create_field_comparison_chart(papers)
        st.plotly_chart(field_fig, use_container_width=True)
    
    def _render_reports_page(self, papers: List[PaperRecord], applicant_name: str):
        """Render reports generation page."""
        st.title("📋 Legal Reports")
        st.markdown("Generate comprehensive reports for visa applications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate HTML Exhibit"):
                html_report = self.report_generator.generate_one_page_exhibit(
                    papers, applicant_name
                )
                st.success("HTML exhibit generated!")
                st.download_button(
                    label="Download HTML Report",
                    data=html_report,
                    file_name=f"{applicant_name}_exhibit.html",
                    mime="text/html"
                )
        
        with col2:
            if st.button("Generate Summary Report"):
                text_report = self.report_generator.generate_summary_report(
                    papers, applicant_name
                )
                st.success("Summary report generated!")
                st.download_button(
                    label="Download Summary",
                    data=text_report,
                    file_name=f"{applicant_name}_summary.txt",
                    mime="text/plain"
                )
    
    def _render_paper_explorer_page(self, papers: List[PaperRecord]):
        """Render paper explorer page."""
        st.title("🔍 Paper Explorer")
        st.markdown("Explore individual papers and their metrics")
        
        # Search and filter
        search_term = st.text_input("Search papers by title or keyword:")
        
        # Filter papers based on search
        if search_term:
            filtered_papers = [
                p for p in papers 
                if search_term.lower() in (p.title or "").lower()
            ]
        else:
            filtered_papers = papers
        
        # Display papers
        for paper in filtered_papers[:20]:  # Limit to first 20
            with st.expander(f"{paper.title} ({paper.citation_count or 0} citations)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Citations", paper.citation_count or 0)
                with col2:
                    st.metric("Year", paper.year or "N/A")
                with col3:
                    st.metric("RCR", f"{paper.rcr:.2f}" if paper.rcr else "N/A")
                
                if paper.abstract:
                    st.text_area("Abstract", paper.abstract, height=100, disabled=True)


def main():
    """Main entry point for dashboard."""
    st.title("CitationMap Dashboard")
    st.markdown("Please load paper data to begin analysis.")


if __name__ == "__main__":
    main()

�