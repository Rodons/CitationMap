"""Disk cache abstraction layer for API responses."""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import diskcache as dc
from pydantic import BaseModel


class CacheConfig(BaseModel):
    """Configuration for cache settings."""
    
    directory: str = ".cache"
    expire_after: int = 604800  # 1 week in seconds
    max_size: str = "1GB"
    
    @property
    def max_size_bytes(self) -> int:
        """Convert max_size string to bytes."""
        size_str = self.max_size.upper()
        if size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        else:
            return int(size_str)


class CacheManager:
    """Manages disk cache for API responses with expiration."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager.
        
        Args:
            config: Cache configuration. Uses defaults if None.
        """
        self.config = config or CacheConfig()
        self.cache_dir = Path(self.config.directory)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize diskcache
        self.cache = dc.Cache(
            str(self.cache_dir),
            size_limit=self.config.max_size_bytes
        )
    
    def _make_key(self, api_name: str, endpoint: str, params: Dict[str, Any]) -> str:
        """Create a cache key from API call parameters.
        
        Args:
            api_name: Name of the API (e.g., 'openalex', 'icite')
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            Cache key string
        """
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        key_data = f"{api_name}:{endpoint}:{sorted_params}"
        
        # Use hash for shorter keys
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def get(self, api_name: str, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve cached response.
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            Cached response data or None if not found/expired
        """
        key = self._make_key(api_name, endpoint, params)
        
        try:
            cached_data = self.cache.get(key)
            if cached_data is None:
                return None
                
            # Check if expired
            cached_time = datetime.fromisoformat(cached_data["timestamp"])
            expires_at = cached_time + timedelta(seconds=self.config.expire_after)
            
            if datetime.now() > expires_at:
                self.cache.delete(key)
                return None
                
            return cached_data["data"]
            
        except (KeyError, ValueError, TypeError):
            # Invalid cache entry, remove it
            self.cache.delete(key)
            return None
    
    def set(self, api_name: str, endpoint: str, params: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Store response in cache.
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint
            params: Request parameters
            data: Response data to cache
        """
        key = self._make_key(api_name, endpoint, params)
        
        cache_entry = {
            "timestamp": datetime.now().isoformat(),
            "api_name": api_name,
            "endpoint": endpoint,
            "params": params,
            "data": data
        }
        
        self.cache.set(key, cache_entry)
    
    def clear(self, api_name: Optional[str] = None) -> int:
        """Clear cache entries.
        
        Args:
            api_name: If provided, only clear entries for this API
            
        Returns:
            Number of entries cleared
        """
        if api_name is None:
            count = len(self.cache)
            self.cache.clear()
            return count
        
        # Clear entries for specific API
        keys_to_delete = []
        for key in self.cache:
            try:
                cached_data = self.cache.get(key)
                if cached_data and cached_data.get("api_name") == api_name:
                    keys_to_delete.append(key)
            except (KeyError, TypeError):
                continue
        
        for key in keys_to_delete:
            self.cache.delete(key)
            
        return len(keys_to_delete)
    
    def stats(self) -> Dict[str, Union[int, str]]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.cache)
        cache_size = sum(self.cache.disk_size.values()) if hasattr(self.cache, 'disk_size') else 0
        
        # Count entries by API
        api_counts = {}
        for key in self.cache:
            try:
                cached_data = self.cache.get(key)
                if cached_data:
                    api_name = cached_data.get("api_name", "unknown")
                    api_counts[api_name] = api_counts.get(api_name, 0) + 1
            except (KeyError, TypeError):
                continue
        
        return {
            "total_entries": total_entries,
            "cache_size_bytes": cache_size,
            "cache_size_mb": round(cache_size / (1024 * 1024), 2),
            "api_breakdown": api_counts,
            "cache_directory": str(self.cache_dir),
            "max_size": self.config.max_size
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cache.close() 