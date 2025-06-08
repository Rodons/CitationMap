"""Tests for data acquisition modules."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime

from citationmap.data_acquisition.cache import CacheManager, CacheConfig
from citationmap.data_acquisition.openalex import OpenAlexClient
from citationmap.data_acquisition.icite import iCiteClient


class TestCacheManager:
    """Test CacheManager functionality."""
    
    def test_cache_config_defaults(self):
        """Test cache configuration defaults."""
        config = CacheConfig()
        assert config.directory == ".cache"
        assert config.expire_after == 604800  # 1 week
        assert config.max_size == "1GB"
    
    def test_cache_config_max_size_bytes(self):
        """Test max_size conversion to bytes."""
        config = CacheConfig(max_size="500MB")
        assert config.max_size_bytes == 500 * 1024 * 1024
        
        config = CacheConfig(max_size="2GB")
        assert config.max_size_bytes == 2 * 1024 * 1024 * 1024
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        cache = CacheManager()
        assert cache.config.directory == ".cache"
        assert cache.cache_dir.name == ".cache"
    
    def test_make_key_consistent(self):
        """Test that cache key generation is consistent."""
        cache = CacheManager()
        
        params1 = {"q": "test", "page": 1}
        params2 = {"page": 1, "q": "test"}  # Same params, different order
        
        key1 = cache._make_key("api", "/endpoint", params1)
        key2 = cache._make_key("api", "/endpoint", params2)
        
        assert key1 == key2
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = CacheManager()
        
        api_name = "test_api"
        endpoint = "/test"
        params = {"q": "test"}
        data = {"result": "test_data"}
        
        # Set data
        cache.set(api_name, endpoint, params, data)
        
        # Get data
        retrieved = cache.get(api_name, endpoint, params)
        assert retrieved == data
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = CacheManager()
        
        result = cache.get("nonexistent", "/endpoint", {"q": "test"})
        assert result is None


class TestOpenAlexClient:
    """Test OpenAlex client functionality."""
    
    def test_initialization(self):
        """Test OpenAlex client initialization."""
        client = OpenAlexClient(email="test@example.com")
        assert client.email == "test@example.com"
        assert client.BASE_URL == "https://api.openalex.org"
    
    @pytest.mark.asyncio
    async def test_parse_work_to_paper_record(self):
        """Test parsing OpenAlex work to PaperRecord."""
        client = OpenAlexClient()
        
        # Mock OpenAlex work data
        work_data = {
            "id": "https://openalex.org/W123456789",
            "title": "Test Paper",
            "doi": "https://doi.org/10.1000/test",
            "publication_date": "2023-01-15",
            "cited_by_count": 42,
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A123",
                        "display_name": "John Doe",
                        "orcid": "https://orcid.org/0000-0000-0000-0000"
                    },
                    "institutions": [
                        {
                            "id": "https://openalex.org/I123",
                            "display_name": "MIT",
                            "country_code": "US",
                            "type": "education"
                        }
                    ],
                    "is_corresponding": True
                }
            ],
            "concepts": [
                {
                    "id": "https://openalex.org/C123",
                    "display_name": "Computer Science",
                    "level": 0,
                    "score": 0.95
                }
            ],
            "host_venue": {
                "display_name": "Nature"
            }
        }
        
        paper = client._parse_work_to_paper_record(work_data)
        
        assert paper.id == "W123456789"
        assert paper.title == "Test Paper"
        assert paper.doi == "10.1000/test"
        assert paper.citation_count == 42
        assert paper.journal == "Nature"
        assert len(paper.authors) == 1
        assert paper.authors[0].display_name == "John Doe"
        assert paper.authors[0].is_corresponding is True
        assert len(paper.authors[0].institutions) == 1
        assert paper.authors[0].institutions[0].display_name == "MIT"
        assert len(paper.fields_of_study) == 1
        assert paper.fields_of_study[0].display_name == "Computer Science"


class TestiCiteClient:
    """Test iCite client functionality."""
    
    def test_initialization(self):
        """Test iCite client initialization."""
        client = iCiteClient()
        assert client.BASE_URL == "https://icite.od.nih.gov/api"
    
    def test_parse_metrics(self):
        """Test parsing iCite response data."""
        client = iCiteClient()
        
        icite_data = {
            "relative_citation_ratio": 2.5,
            "field_citation_rate": 1.8,
            "citation_count": 50,
            "citations_per_year": 10.0,
            "provisional": False,
            "year": 2020,
            "journal": "Nature"
        }
        
        parsed = client.parse_metrics(icite_data)
        
        assert parsed["rcr"] == 2.5
        assert parsed["fcr"] == 1.8
        assert parsed["citation_count"] == 50
        assert parsed["provisional"] is False
        assert parsed["percentile"] == 90.0  # RCR 2.5 maps to 90th percentile
    
    def test_calculate_percentile(self):
        """Test RCR to percentile conversion."""
        client = iCiteClient()
        
        assert client._calculate_percentile(None) is None
        assert client._calculate_percentile(4.5) == 95.0
        assert client._calculate_percentile(2.5) == 90.0
        assert client._calculate_percentile(1.5) == 75.0
        assert client._calculate_percentile(1.0) == 50.0
        assert client._calculate_percentile(0.5) == 25.0
        assert client._calculate_percentile(0.1) == 10.0
    
    @pytest.mark.asyncio
    async def test_enrich_papers_with_metrics(self):
        """Test enriching papers with iCite metrics."""
        # Mock the HTTP request
        with patch.object(iCiteClient, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "data": [
                    {
                        "doi": "10.1000/test",
                        "relative_citation_ratio": 2.0,
                        "field_citation_rate": 1.5,
                        "citation_count": 30,
                        "provisional": False
                    }
                ]
            }
            
            client = iCiteClient()
            
            papers = [
                {"doi": "10.1000/test", "title": "Test Paper"},
                {"doi": "10.1000/other", "title": "Other Paper"}
            ]
            
            enriched = await client.enrich_papers_with_metrics(papers, id_field="doi")
            
            assert len(enriched) == 2
            assert enriched[0]["rcr"] == 2.0
            assert enriched[0]["fcr"] == 1.5
            assert enriched[0]["percentile"] == 85.0
            assert "rcr" not in enriched[1]  # No iCite data for second paper


@pytest.mark.asyncio
async def test_integration_example():
    """Integration test example using mocked responses."""
    # This would test the full pipeline with mocked API responses
    with patch('httpx.AsyncClient.get') as mock_get:
        # Mock OpenAlex response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "https://openalex.org/W123",
                    "title": "Test Paper",
                    "doi": "https://doi.org/10.1000/test",
                    "cited_by_count": 10,
                    "authorships": [],
                    "concepts": [],
                    "host_venue": {"display_name": "Test Journal"}
                }
            ],
            "meta": {"count": 1}
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        async with OpenAlexClient() as client:
            papers = await client.fetch_author_papers("test_author")
            assert len(papers) == 1
            assert papers[0].title == "Test Paper" 