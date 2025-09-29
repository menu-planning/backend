"""
FastAPI thread-safe authentication caching.

This module provides request-scoped caching for authentication data to improve
performance and reduce database calls for user authentication and authorization.
"""

import logging
from typing import Any
from datetime import datetime, timezone, timedelta
from threading import RLock
from dataclasses import dataclass, field

from .user_context import UserContext

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry[T]:
    """Cache entry with value, expiration, and metadata."""
    
    value: T
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=15))
    access_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)


class RequestScopedAuthCache:
    """
    Thread-safe request-scoped authentication cache.
    
    This cache stores authentication data for the duration of a request,
    providing fast access to user context, roles, and permissions without
    repeated database calls.
    """
    
    def __init__(self, default_ttl_seconds: int = 900):  # 15 minutes default
        """
        Initialize the request-scoped cache.
        
        Args:
            default_ttl_seconds: Default time-to-live for cache entries in seconds
        """
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: dict[str, CacheEntry[Any]] = {}
        self._lock = RLock()
        self._request_id: str | None = None
        self._created_at = datetime.now(timezone.utc)
    
    def set_request_id(self, request_id: str) -> None:
        """
        Set the request ID for this cache instance.
        
        Args:
            request_id: Unique identifier for the current request
        """
        with self._lock:
            self._request_id = request_id
            logger.debug(
                "Request-scoped cache initialized",
                extra={
                    "request_id": request_id,
                    "cache_created_at": self._created_at.isoformat(),
                }
            )
    
    def get(self, key: str) -> Any | None:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            if entry.is_expired():
                del self._cache[key]
                logger.debug(
                    "Cache entry expired and removed",
                    extra={
                        "key": key,
                        "request_id": self._request_id,
                        "expired_at": entry.expires_at.isoformat(),
                    }
                )
                return None
            
            entry.touch()
            
            logger.debug(
                "Cache hit",
                extra={
                    "key": key,
                    "request_id": self._request_id,
                    "access_count": entry.access_count,
                }
            )
            
            return entry.value
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: int | None = None
    ) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
        """
        with self._lock:
            ttl = ttl_seconds or self.default_ttl_seconds
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=expires_at,
            )
            
            logger.debug(
                "Cache entry set",
                extra={
                    "key": key,
                    "request_id": self._request_id,
                    "ttl_seconds": ttl,
                    "expires_at": expires_at.isoformat(),
                }
            )
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(
                    "Cache entry deleted",
                    extra={
                        "key": key,
                        "request_id": self._request_id,
                    }
                )
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            entry_count = len(self._cache)
            self._cache.clear()
            
            logger.debug(
                "Cache cleared",
                extra={
                    "request_id": self._request_id,
                    "entries_cleared": entry_count,
                }
            )
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match against cache keys
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys() 
                if pattern in key
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            logger.debug(
                "Cache entries invalidated by pattern",
                extra={
                    "pattern": pattern,
                    "request_id": self._request_id,
                    "entries_invalidated": len(keys_to_delete),
                }
            )
            
            return len(keys_to_delete)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
            active_entries = total_entries - expired_entries
            
            total_access_count = sum(entry.access_count for entry in self._cache.values())
            avg_access_count = total_access_count / total_entries if total_entries > 0 else 0
            
            return {
                "request_id": self._request_id,
                "created_at": self._created_at.isoformat(),
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "total_access_count": total_access_count,
                "avg_access_count": round(avg_access_count, 2),
                "cache_age_seconds": (now - self._created_at).total_seconds(),
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.
        
        Returns:
            Number of expired entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(
                    "Expired cache entries cleaned up",
                    extra={
                        "request_id": self._request_id,
                        "entries_removed": len(expired_keys),
                    }
                )
            
            return len(expired_keys)


class UserContextCache:
    """
    Specialized cache for user context data.
    
    This cache provides optimized storage and retrieval for user context
    objects with role and permission data.
    """
    
    def __init__(self, auth_cache: RequestScopedAuthCache):
        """
        Initialize user context cache.
        
        Args:
            auth_cache: Request-scoped authentication cache instance
        """
        self.auth_cache = auth_cache
        self._user_prefix = "user_context:"
        self._roles_prefix = "user_roles:"
        self._permissions_prefix = "user_permissions:"
    
    def get_user_context(self, user_id: str) -> UserContext | None:
        """
        Get user context from cache.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserContext if found in cache, None otherwise
        """
        key = f"{self._user_prefix}{user_id}"
        return self.auth_cache.get(key)
    
    def set_user_context(
        self, 
        user_id: str, 
        user_context: UserContext,
        ttl_seconds: int | None = None
    ) -> None:
        """
        Set user context in cache.
        
        Args:
            user_id: User identifier
            user_context: User context to cache
            ttl_seconds: Time-to-live in seconds
        """
        key = f"{self._user_prefix}{user_id}"
        self.auth_cache.set(key, user_context, ttl_seconds)
    
    def get_user_roles(self, user_id: str, context: str = "fastapi") -> list[str] | None:
        """
        Get user roles from cache.
        
        Args:
            user_id: User identifier
            context: Context for role filtering
            
        Returns:
            List of roles if found in cache, None otherwise
        """
        key = f"{self._roles_prefix}{user_id}:{context}"
        return self.auth_cache.get(key)
    
    def set_user_roles(
        self, 
        user_id: str, 
        roles: list[str], 
        context: str = "fastapi",
        ttl_seconds: int | None = None
    ) -> None:
        """
        Set user roles in cache.
        
        Args:
            user_id: User identifier
            roles: List of roles to cache
            context: Context for role filtering
            ttl_seconds: Time-to-live in seconds
        """
        key = f"{self._roles_prefix}{user_id}:{context}"
        self.auth_cache.set(key, roles, ttl_seconds)
    
    def get_user_permissions(
        self, 
        user_id: str, 
        context: str = "fastapi"
    ) -> list[str] | None:
        """
        Get user permissions from cache.
        
        Args:
            user_id: User identifier
            context: Context for permission filtering
            
        Returns:
            List of permissions if found in cache, None otherwise
        """
        key = f"{self._permissions_prefix}{user_id}:{context}"
        return self.auth_cache.get(key)
    
    def set_user_permissions(
        self, 
        user_id: str, 
        permissions: list[str], 
        context: str = "fastapi",
        ttl_seconds: int | None = None
    ) -> None:
        """
        Set user permissions in cache.
        
        Args:
            user_id: User identifier
            permissions: List of permissions to cache
            context: Context for permission filtering
            ttl_seconds: Time-to-live in seconds
        """
        key = f"{self._permissions_prefix}{user_id}:{context}"
        self.auth_cache.set(key, permissions, ttl_seconds)
    
    def invalidate_user(self, user_id: str) -> int:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of entries invalidated
        """
        patterns = [
            f"{self._user_prefix}{user_id}",
            f"{self._roles_prefix}{user_id}:",
            f"{self._permissions_prefix}{user_id}:",
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += self.auth_cache.invalidate_pattern(pattern)
        
        logger.debug(
            "User cache entries invalidated",
            extra={
                "user_id": user_id,
                "entries_invalidated": total_invalidated,
                "request_id": self.auth_cache._request_id,
            }
        )
        
        return total_invalidated
    
    def invalidate_user_context(self, user_id: str) -> bool:
        """
        Invalidate user context cache entry.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if entry was deleted, False if not found
        """
        key = f"{self._user_prefix}{user_id}"
        return self.auth_cache.delete(key)
    
    def invalidate_user_roles(self, user_id: str, context: str = "fastapi") -> bool:
        """
        Invalidate user roles cache entry.
        
        Args:
            user_id: User identifier
            context: Context for role filtering
            
        Returns:
            True if entry was deleted, False if not found
        """
        key = f"{self._roles_prefix}{user_id}:{context}"
        return self.auth_cache.delete(key)
    
    def invalidate_user_permissions(self, user_id: str, context: str = "fastapi") -> bool:
        """
        Invalidate user permissions cache entry.
        
        Args:
            user_id: User identifier
            context: Context for permission filtering
            
        Returns:
            True if entry was deleted, False if not found
        """
        key = f"{self._permissions_prefix}{user_id}:{context}"
        return self.auth_cache.delete(key)


# Global cache instances (singleton pattern)
_auth_cache_instance:RequestScopedAuthCache | None = None
_user_context_cache_instance: UserContextCache | None = None


def get_auth_cache() -> RequestScopedAuthCache:
    """
    Get or create the global authentication cache instance.
    
    Returns:
        RequestScopedAuthCache: Global cache instance
        
    Notes:
        Uses singleton pattern to avoid recreating cache instances
        across requests.
    """
    global _auth_cache_instance
    
    if _auth_cache_instance is None:
        _auth_cache_instance = RequestScopedAuthCache()
    
    return _auth_cache_instance


def get_user_context_cache() -> UserContextCache:
    """
    Get or create the global user context cache instance.
    
    Returns:
        UserContextCache: Global cache instance
        
    Notes:
        Uses singleton pattern to avoid recreating cache instances
        across requests.
    """
    global _user_context_cache_instance
    
    if _user_context_cache_instance is None:
        auth_cache = get_auth_cache()
        _user_context_cache_instance = UserContextCache(auth_cache)
    
    return _user_context_cache_instance


def clear_global_caches() -> None:
    """Clear all global cache instances."""
    global _auth_cache_instance, _user_context_cache_instance
    
    if _auth_cache_instance:
        _auth_cache_instance.clear()
    
    _auth_cache_instance = None
    _user_context_cache_instance = None
    
    logger.info("Global authentication caches cleared")
