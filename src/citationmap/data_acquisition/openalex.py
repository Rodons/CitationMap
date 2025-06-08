"""OpenAlex API client with async support, pagination, and caching."""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
from datetime import datetime
from urllib.parse import urlencode
import logging

from .cache import CacheManager
from ..core.models import PaperRecord, Author, Institution, FieldOfStudy

logger = logging.getLogger(__name__)


class OpenAlexClient:
    """Async client for OpenAlex API with caching and pagination."""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(
        self,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_manager: Optional[CacheManager] = None,
        rate_limit: int = 100,  # requests per minute
    ):
        """Initialize OpenAlex client.
        
        Args:
            email: Your email for polite access
            api_key: Optional API key for higher rate limits
            cache_manager: Cache manager instance
            rate_limit: Requests per minute limit
        """
        self.email = email
        self.api_key = api_key
        self.cache = cache_manager or CacheManager()
        self.rate_limit = rate_limit
        
        # Setup HTTP client
        headers = {
            "User-Agent": "CitationMap/0.1.0 (https://github.com/Rodons/CitationMap)"
        }
        if email:
            headers["User-Agent"] += f" mailto:{email}"
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
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
            endpoint: API endpoint (e.g., "/works")
            params: Query parameters
            
        Returns:
            API response data
        """
        # Check cache first
        cached_response = self.cache.get("openalex", endpoint, params)
        if cached_response:
            logger.debug(f"Cache hit for {endpoint} with params {params}")
            return cached_response
        
        # Apply rate limiting
        await self._rate_limit()
        
        # Add email to params if available
        if self.email and "mailto" not in params:
            params["mailto"] = self.email
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            logger.debug(f"Making request to {url} with params {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            self.cache.set("openalex", endpoint, params, data)
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise
    
    async def get_works_by_author(
        self, 
        author_id: str,
        limit: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get works by author with pagination.
        
        Args:
            author_id: OpenAlex author ID or ORCID
            limit: Maximum number of works to return (None for all)
            
        Yields:
            Work objects from OpenAlex
        """
        per_page = 200  # Max per page for OpenAlex
        page = 1
        total_yielded = 0
        
        while True:
            params = {
                "filter": f"author.id:{author_id}",
                "per-page": per_page,
                "page": page,
                "sort": "cited_by_count:desc"
            }
            
            response = await self._make_request("/works", params)
            
            works = response.get("results", [])
            if not works:
                break
            
            for work in works:
                if limit and total_yielded >= limit:
                    return
                yield work
                total_yielded += 1
            
            # Check if there are more pages
            meta = response.get("meta", {})
            if page >= meta.get("count", 0) // per_page + 1:
                break
            
            page += 1
    
    async def get_work_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Get a single work by DOI.
        
        Args:
            doi: DOI of the work
            
        Returns:
            Work object or None if not found
        """
        params = {"filter": f"doi:{doi}"}
        
        try:
            response = await self._make_request("/works", params)
            works = response.get("results", [])
            return works[0] if works else None
        except Exception as e:
            logger.error(f"Error fetching work by DOI {doi}: {e}")
            return None
    
    async def get_works_by_ids(self, work_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple works by their OpenAlex IDs.
        
        Args:
            work_ids: List of OpenAlex work IDs
            
        Returns:
            List of work objects
        """
        if not work_ids:
            return []
        
        # OpenAlex allows filtering by multiple IDs
        id_filter = "|".join(work_ids)
        params = {
            "filter": f"openalex_id:{id_filter}",
            "per-page": min(200, len(work_ids))
        }
        
        response = await self._make_request("/works", params)
        return response.get("results", [])
    
    async def get_citations(
        self, 
        work_id: str,
        limit: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get citations for a work.
        
        Args:
            work_id: OpenAlex work ID
            limit: Maximum number of citations to return
            
        Yields:
            Citing work objects
        """
        per_page = 200
        page = 1
        total_yielded = 0
        
        while True:
            params = {
                "filter": f"cites:{work_id}",
                "per-page": per_page,
                "page": page,
                "sort": "publication_date:desc"
            }
            
            response = await self._make_request("/works", params)
            
            citing_works = response.get("results", [])
            if not citing_works:
                break
            
            for citing_work in citing_works:
                if limit and total_yielded >= limit:
                    return
                yield citing_work
                total_yielded += 1
            
            # Check if there are more pages
            meta = response.get("meta", {})
            if page >= meta.get("count", 0) // per_page + 1:
                break
            
            page += 1
    
    def _parse_work_to_paper_record(self, work: Dict[str, Any]) -> PaperRecord:
        """Convert OpenAlex work to PaperRecord.
        
        Args:
            work: OpenAlex work object
            
        Returns:
            PaperRecord instance
        """
        # Extract basic info
        work_id = work.get("id", "").replace("https://openalex.org/", "")
        title = work.get("title", "")
        
        # Extract DOI
        doi = None
        if work.get("doi"):
            doi = work["doi"].replace("https://doi.org/", "")
        
        # Extract publication date
        pub_date = None
        if work.get("publication_date"):
            try:
                pub_date = datetime.fromisoformat(work["publication_date"])
            except ValueError:
                pass
        
        # Extract authors with institutions
        authors = []
        for authorship in work.get("authorships", []):
            author_data = authorship.get("author", {})
            
            # Parse institutions
            institutions = []
            for inst_data in authorship.get("institutions", []):
                institution = Institution(
                    id=inst_data.get("id", "").replace("https://openalex.org/", ""),
                    display_name=inst_data.get("display_name", ""),
                    country_code=inst_data.get("country_code"),
                    type=inst_data.get("type")
                )
                institutions.append(institution)
            
            author = Author(
                id=author_data.get("id", "").replace("https://openalex.org/", ""),
                display_name=author_data.get("display_name", ""),
                orcid=author_data.get("orcid"),
                institutions=institutions,
                is_corresponding=authorship.get("is_corresponding", False)
            )
            authors.append(author)
        
        # Extract fields of study
        fields_of_study = []
        for concept in work.get("concepts", []):
            field = FieldOfStudy(
                id=concept.get("id", "").replace("https://openalex.org/", ""),
                display_name=concept.get("display_name", ""),
                level=concept.get("level", 0),
                score=concept.get("score", 0.0)
            )
            fields_of_study.append(field)
        
        # Primary field is typically the highest scoring level 0 or 1 concept
        primary_field = None
        for field in fields_of_study:
            if field.level <= 1:
                primary_field = field.display_name
                break
        
        return PaperRecord(
            id=work_id,
            doi=doi,
            title=title,
            authors=authors,
            publication_date=pub_date,
            journal=work.get("host_venue", {}).get("display_name"),
            venue=work.get("host_venue", {}).get("display_name"),
            citation_count=work.get("cited_by_count", 0),
            fields_of_study=fields_of_study,
            primary_field=primary_field
        )
    
    async def fetch_author_papers(self, author_id: str) -> List[PaperRecord]:
        """Fetch all papers for an author.
        
        Args:
            author_id: OpenAlex author ID or ORCID
            
        Returns:
            List of PaperRecord objects
        """
        papers = []
        async for work in self.get_works_by_author(author_id):
            try:
                paper = self._parse_work_to_paper_record(work)
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse work {work.get('id', 'unknown')}: {e}")
        
        return papers 