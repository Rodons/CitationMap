"""iCite API client for RCR metrics and field percentiles."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx

from .cache import CacheManager

logger = logging.getLogger(__name__)


class iCiteClient:
    """Client for NIH iCite API to get RCR and field citation metrics."""
    
    BASE_URL = "https://icite.od.nih.gov/api"
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        rate_limit: int = 200,  # requests per minute
    ):
        """Initialize iCite client.
        
        Args:
            cache_manager: Cache manager instance
            rate_limit: Requests per minute limit
        """
        self.cache = cache_manager or CacheManager()
        self.rate_limit = rate_limit
        
        # Setup HTTP client
        headers = {
            "User-Agent": "CitationMap/0.1.0 (https://github.com/Rodons/CitationMap)",
            "Content-Type": "application/json"
        }
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=3)
        )
        
        # Rate limiting
        self._semaphore = asyncio.Semaphore(rate_limit // 60)  # Per second
        self._last_request_time = 0.0
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def _rate_limit(self) -> None:
        """Implement rate limiting."""
        async with self._semaphore:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self._last_request_time
            min_interval = 60.0 / self.rate_limit
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
            
            self._last_request_time = asyncio.get_event_loop().time()
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make API request with caching and rate limiting.
        
        Args:
            endpoint: API endpoint (e.g., "/pubs")
            params: Query parameters
            
        Returns:
            API response data
        """
        # Check cache first
        cached_response = self.cache.get("icite", endpoint, params)
        if cached_response:
            logger.debug(f"Cache hit for iCite {endpoint} with params {params}")
            return cached_response
        
        # Apply rate limiting
        await self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            logger.debug(f"Making iCite request to {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            self.cache.set("icite", endpoint, params, data)
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error for iCite {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for iCite {url}: {e}")
            raise
    
    async def get_metrics_by_pmids(self, pmids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get iCite metrics for papers by PMID.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            Dictionary mapping PMID to metrics data
        """
        if not pmids:
            return {}
        
        # iCite accepts up to 1000 PMIDs per request
        batch_size = 1000
        all_metrics = {}
        
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i + batch_size]
            pmid_list = ",".join(batch_pmids)
            
            params = {
                "pmids": pmid_list,
                "format": "json"
            }
            
            try:
                response = await self._make_request("/pubs", params)
                
                for paper_data in response.get("data", []):
                    pmid = str(paper_data.get("pmid"))
                    if pmid:
                        all_metrics[pmid] = paper_data
                        
            except Exception as e:
                logger.error(f"Error fetching iCite data for PMIDs {batch_pmids}: {e}")
                # Continue with other batches
                continue
        
        return all_metrics
    
    async def get_metrics_by_dois(self, dois: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get iCite metrics for papers by DOI.
        
        Args:
            dois: List of DOIs
            
        Returns:
            Dictionary mapping DOI to metrics data
        """
        if not dois:
            return {}
        
        # iCite accepts up to 1000 DOIs per request
        batch_size = 1000
        all_metrics = {}
        
        for i in range(0, len(dois), batch_size):
            batch_dois = dois[i:i + batch_size]
            doi_list = ",".join(batch_dois)
            
            params = {
                "dois": doi_list,
                "format": "json"
            }
            
            try:
                response = await self._make_request("/pubs", params)
                
                for paper_data in response.get("data", []):
                    doi = paper_data.get("doi")
                    if doi:
                        all_metrics[doi] = paper_data
                        
            except Exception as e:
                logger.error(f"Error fetching iCite data for DOIs {batch_dois}: {e}")
                # Continue with other batches
                continue
        
        return all_metrics
    
    def parse_metrics(self, icite_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """Parse iCite response into standardized metrics.
        
        Args:
            icite_data: Raw iCite response for a single paper
            
        Returns:
            Dictionary with parsed metrics
        """
        return {
            "rcr": icite_data.get("relative_citation_ratio"),
            "fcr": icite_data.get("field_citation_rate"),
            "citation_count": icite_data.get("citation_count"),
            "citations_per_year": icite_data.get("citations_per_year"),
            "expected_citations_per_year": icite_data.get("expected_citations_per_year"),
            "field_citation_rate": icite_data.get("field_citation_rate"),
            "provisional": icite_data.get("provisional", True),
            "year": icite_data.get("year"),
            "journal": icite_data.get("journal"),
            "percentile": self._calculate_percentile(icite_data.get("relative_citation_ratio"))
        }
    
    def _calculate_percentile(self, rcr: Optional[float]) -> Optional[float]:
        """Calculate approximate percentile from RCR.
        
        RCR > 1.0 means above average field performance.
        This is a rough approximation - actual percentiles would need
        field-specific distributions.
        
        Args:
            rcr: Relative Citation Ratio
            
        Returns:
            Approximate percentile (0-100)
        """
        if rcr is None:
            return None
        
        # Rough mapping based on RCR distribution characteristics
        if rcr >= 4.0:
            return 95.0
        elif rcr >= 2.5:
            return 90.0
        elif rcr >= 2.0:
            return 85.0
        elif rcr >= 1.5:
            return 75.0
        elif rcr >= 1.0:
            return 50.0
        elif rcr >= 0.5:
            return 25.0
        else:
            return 10.0
    
    async def enrich_papers_with_metrics(
        self, 
        papers: List[Dict[str, Any]], 
        id_field: str = "doi"
    ) -> List[Dict[str, Any]]:
        """Enrich papers with iCite metrics.
        
        Args:
            papers: List of paper objects with identifiers
            id_field: Field to use for lookup ("doi" or "pmid")
            
        Returns:
            Papers enriched with iCite metrics
        """
        # Extract identifiers
        identifiers = []
        for paper in papers:
            identifier = paper.get(id_field)
            if identifier:
                identifiers.append(str(identifier))
        
        if not identifiers:
            logger.warning("No valid identifiers found for iCite lookup")
            return papers
        
        # Fetch metrics
        if id_field == "doi":
            metrics_data = await self.get_metrics_by_dois(identifiers)
        elif id_field == "pmid":
            metrics_data = await self.get_metrics_by_pmids(identifiers)
        else:
            logger.error(f"Unsupported id_field: {id_field}")
            return papers
        
        # Enrich papers
        enriched_papers = []
        for paper in papers:
            identifier = paper.get(id_field)
            if identifier and str(identifier) in metrics_data:
                icite_data = metrics_data[str(identifier)]
                parsed_metrics = self.parse_metrics(icite_data)
                
                # Add metrics to paper
                enriched_paper = paper.copy()
                enriched_paper.update({
                    "rcr": parsed_metrics["rcr"],
                    "fcr": parsed_metrics["fcr"],
                    "percentile": parsed_metrics["percentile"],
                    "icite_citation_count": parsed_metrics["citation_count"],
                    "provisional": parsed_metrics["provisional"]
                })
                enriched_papers.append(enriched_paper)
            else:
                enriched_papers.append(paper)
        
        return enriched_papers 