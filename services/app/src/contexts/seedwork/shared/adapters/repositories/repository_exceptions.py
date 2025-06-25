"""
Enhanced repository exception hierarchy with structured error context.

This module provides enhanced exception classes for repository operations
with detailed context information for better error handling and debugging.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Generic, Any, Dict, Optional
import uuid
from datetime import datetime, timezone

if TYPE_CHECKING:
    from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import SaGenericRepository
    R = TypeVar("R", bound=SaGenericRepository)
else:
    # Fallback at runtime for importability
    R = TypeVar("R")


class RepositoryException(Generic[R], Exception):
    """
    Enhanced base exception class for repository operations.
    
    Provides structured error context including repository type, operation,
    and additional context information for better error handling and debugging.
    
    Attributes:
        repository_type: The type/class name of the repository where the error occurred
        operation: The operation being performed when the error occurred (e.g., 'query', 'save', 'delete')
        context: Additional context information as key-value pairs
        correlation_id: Unique identifier for tracking related operations
        timestamp: When the exception occurred
        message: Human-readable error message
        repository: The repository instance (for backward compatibility)
    """
    
    def __init__(
        self,
        message: str,
        repository: R,
        *,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Initialize repository exception with enhanced context.
        
        Args:
            message: Human-readable error description
            repository: The repository instance where the error occurred
            operation: The operation being performed (e.g., 'query', 'save', 'delete')
            context: Additional context information as key-value pairs
            correlation_id: Optional correlation ID for tracking (auto-generated if not provided)
        """
        super().__init__(message)
        self.message = message
        self.repository = repository
        self.repository_type = repository.__class__.__name__ if repository else "Unknown"
        self.operation = operation
        self.context = context or {}
        self.correlation_id = correlation_id or uuid.uuid4().hex[:8]
        self.timestamp = datetime.now(timezone.utc)
    
    def __str__(self) -> str:
        """Enhanced string representation with context."""
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return (
            f"{self.__class__.__name__}: {self.message} "
            f"[repository={self.repository_type}, operation={self.operation}, "
            f"correlation_id={self.correlation_id}"
            f"{', ' + context_str if context_str else ''}]"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for structured logging.
        
        Returns:
            Dictionary representation suitable for structured logging
        """
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "repository_type": self.repository_type,
            "operation": self.operation,
            "context": self.context,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def add_context(self, key: str, value: Any) -> None:
        """
        Add additional context information to the exception.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value


class RepositoryQueryException(RepositoryException[R]):
    """
    Exception raised during repository query operations.
    
    Includes additional context specific to query operations such as
    filter values, SQL query, and execution time.
    """
    
    def __init__(
        self,
        message: str,
        repository: R,
        *,
        filter_values: Optional[Dict[str, Any]] = None,
        sql_query: Optional[str] = None,
        execution_time: Optional[float] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Initialize query exception with query-specific context.
        
        Args:
            message: Human-readable error description
            repository: The repository instance where the error occurred
            filter_values: The filter values that caused the error
            sql_query: The SQL query that failed (if available)
            execution_time: Query execution time in seconds
            correlation_id: Optional correlation ID for tracking
        """
        context = {
            "filter_values": filter_values,
            "sql_query": sql_query,
            "execution_time": execution_time,
        }
        # Remove None values from context
        context = {k: v for k, v in context.items() if v is not None}
        
        super().__init__(
            message=message,
            repository=repository,
            operation="query",
            context=context,
            correlation_id=correlation_id,
        )
        
        # Store as individual attributes for easy access
        self.filter_values = filter_values or {}
        self.sql_query = sql_query
        self.execution_time = execution_time


class FilterValidationException(RepositoryException[R]):
    """
    Exception raised when filter validation fails.
    
    Includes information about invalid filters and suggested alternatives.
    """
    
    def __init__(
        self,
        message: str,
        repository: R,
        *,
        invalid_filters: Optional[list[str]] = None,
        suggested_filters: Optional[list[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Initialize filter validation exception.
        
        Args:
            message: Human-readable error description
            repository: The repository instance where the error occurred
            invalid_filters: List of invalid filter names
            suggested_filters: List of suggested valid filter names
            correlation_id: Optional correlation ID for tracking
        """
        context = {
            "invalid_filters": invalid_filters or [],
            "suggested_filters": suggested_filters or [],
        }
        
        super().__init__(
            message=message,
            repository=repository,
            operation="filter_validation",
            context=context,
            correlation_id=correlation_id,
        )
        
        # Store as individual attributes for easy access
        self.invalid_filters = invalid_filters or []
        self.suggested_filters = suggested_filters or []


class JoinException(RepositoryException[R]):
    """
    Exception raised when join operations fail.
    
    Includes information about the join path and relationship errors.
    """
    
    def __init__(
        self,
        message: str,
        repository: R,
        *,
        join_path: Optional[str] = None,
        relationship_error: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Initialize join exception.
        
        Args:
            message: Human-readable error description
            repository: The repository instance where the error occurred
            join_path: The join path that failed
            relationship_error: Description of the relationship error
            correlation_id: Optional correlation ID for tracking
        """
        context = {
            "join_path": join_path,
            "relationship_error": relationship_error,
        }
        # Remove None values from context
        context = {k: v for k, v in context.items() if v is not None}
        
        super().__init__(
            message=message,
            repository=repository,
            operation="join",
            context=context,
            correlation_id=correlation_id,
        )
        
        # Store as individual attributes for easy access
        self.join_path = join_path
        self.relationship_error = relationship_error


class EntityMappingException(RepositoryException[R]):
    """
    Exception raised when entity mapping fails.
    
    Includes context about domain objects and SQLAlchemy objects involved.
    """
    
    def __init__(
        self,
        message: str,
        repository: R,
        *,
        domain_obj: Optional[Any] = None,
        sa_obj: Optional[Any] = None,
        mapping_direction: str = "unknown",
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Initialize entity mapping exception.
        
        Args:
            message: Human-readable error description
            repository: The repository instance where the error occurred
            domain_obj: The domain object involved in mapping
            sa_obj: The SQLAlchemy object involved in mapping
            mapping_direction: Direction of mapping ('domain_to_sa' or 'sa_to_domain')
            correlation_id: Optional correlation ID for tracking
        """
        context = {
            "domain_obj_type": type(domain_obj).__name__ if domain_obj else None,
            "sa_obj_type": type(sa_obj).__name__ if sa_obj else None,
            "mapping_direction": mapping_direction,
        }
        # Remove None values from context
        context = {k: v for k, v in context.items() if v is not None}
        
        super().__init__(
            message=message,
            repository=repository,
            operation="entity_mapping",
            context=context,
            correlation_id=correlation_id,
        )
        
        # Store as individual attributes for easy access
        self.domain_obj = domain_obj
        self.sa_obj = sa_obj
        self.mapping_direction = mapping_direction


# Backward compatibility aliases - re-export existing exceptions
# This allows gradual migration from old to new exception classes
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
    FilterNotAllowedError,
)

__all__ = [
    "RepositoryException",
    "RepositoryQueryException", 
    "FilterValidationException",
    "JoinException",
    "EntityMappingException",
    # Backward compatibility
    "EntityNotFoundException",
    "MultipleEntitiesFoundException", 
    "FilterNotAllowedError",
] 