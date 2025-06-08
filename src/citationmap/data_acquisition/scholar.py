"""Google Scholar scraper (fallback for when other APIs are unavailable)."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from urllib.parse import quote_plus
import re

from .cache import CacheManager

logger = logging.getLogger(__name__)


class GoogleScholarClient:
    """Basic Google Scholar scraper for fallback functionality."""
    
    BASE_URL = "https://scholar.google.com"
    
    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        rate_limit: int = 10,  # Conservative rate limit for scraping
    ):
        """Initialize Google Scholar client.
        
        Args:
            cache_manager: Cache manager instance
            rate_limit: Requests per minute limit (very conservative)
        """
        self.cache = cache_manager or CacheManager()
        self.rate_limit = rate_limit
        
        # Setup HTTP client with browser-like headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
            follow_redirects=True
        )
        
        # Rate limiting
        self._semaphore = asyncio.Semaphore(1)  # Very conservative
        self._last_request_time = 0.0
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    async def _rate_limit(self) -> None:
        """Implement conservative rate limiting."""
        async with self._semaphore:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self._last_request_time
            min_interval = 60.0 / self.rate_limit
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
            
            self._last_request_time = asyncio.get_event_loop().time()
    
    async def search_author_papers(
        self, 
        author_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for papers by author name.
        
        Args:
            author_name: Name of the author to search for
            limit: Maximum number of papers to return
            
        Returns:
            List of paper metadata dictionaries
            
        Note:
            This is a basic implementation for fallback use only.
            Prefer OpenAlex API for production use.
        """
        # Check cache first
        cache_key = f"author_search_{author_name}"
        cached_response = self.cache.get("scholar", "/search", {"author": author_name})
        if cached_response:
            logger.debug(f"Cache hit for Scholar author search: {author_name}")
            return cached_response
        
        await self._rate_limit()
        
        # Construct search URL
        query = f"author:\"{author_name}\""
        encoded_query = quote_plus(query)
        url = f"{self.BASE_URL}/scholar?q={encoded_query}&hl=en&as_sdt=0%2C5"
        
        try:
            logger.debug(f"Searching Google Scholar for author: {author_name}")
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Basic HTML parsing (this is fragile and for demo purposes only)
            papers = self._parse_search_results(response.text, limit)
            
            # Cache the results
            self.cache.set("scholar", "/search", {"author": author_name}, papers)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching Scholar for {author_name}: {e}")
            return []
    
    def _parse_search_results(self, html: str, limit: int) -> List[Dict[str, Any]]:
        """Basic parsing of Google Scholar search results.
        
        Args:
            html: HTML content from Scholar search
            limit: Maximum papers to extract
            
        Returns:
            List of paper dictionaries
            
        Note:
            This is a minimal implementation for demonstration.
            Real scraping would need more robust parsing.
        """
        papers = []
        
        # Very basic regex patterns (fragile, for demo only)
        title_pattern = r'<h3[^>]*><a[^>]*>([^<]+)</a></h3>'
        citation_pattern = r'Cited by (\d+)'
        year_pattern = r'(\d{4})'
        
        titles = re.findall(title_pattern, html)
        citations = re.findall(citation_pattern, html)
        years = re.findall(year_pattern, html)
        
        for i, title in enumerate(titles[:limit]):
            paper = {
                "title": title.strip(),
                "citation_count": int(citations[i]) if i < len(citations) else 0,
                "year": int(years[i]) if i < len(years) else None,
                "source": "google_scholar"
            }
            papers.append(paper)
        
        return papers
    
    async def get_citation_count(self, title: str) -> Optional[int]:
        """Get citation count for a specific paper by title.
        
        Args:
            title: Paper title to search for
            
        Returns:
            Citation count or None if not found
        """
        papers = await self.search_author_papers(f'"{title}"', limit=1)
        if papers and papers[0]["title"].lower() in title.lower():
            return papers[0].get("citation_count")
        return None 