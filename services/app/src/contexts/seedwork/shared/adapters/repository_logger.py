"""
Structured repository logging with correlation tracking and performance monitoring.

This module provides enhanced logging capabilities for repository operations
with automatic correlation ID generation, structured context, and performance tracking.
"""

from __future__ import annotations
import uuid
import time
import structlog
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, AsyncGenerator, List
from datetime import datetime, timezone

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.logging.logger import StructlogFactory, correlation_id_ctx


class RepositoryLogger:
    """
    Enhanced repository logger using structlog for structured logging.
    
    Provides correlation ID generation, context management, performance tracking,
    and integration with existing logging infrastructure.
    
    Features:
    - Structured logging with correlation ID tracking
    - Query performance monitoring with execution time tracking
    - Memory usage monitoring (when psutil is available)
    - Filter and join operation logging
    - Warning detection for performance issues
    - Debug logging for SQL query construction
    """
    
    def __init__(self, logger_name: str = "repository", correlation_id: Optional[str] = None):
        """
        Initialize repository logger with structlog.
        
        Args:
            logger_name: Name for the logger instance
            correlation_id: Optional correlation ID (auto-generated if not provided)
        """
        # Ensure structlog is configured
        StructlogFactory.configure()
        
        self.logger = structlog.get_logger(logger_name)
        self.correlation_id = correlation_id or uuid.uuid4().hex[:8]
        self.logger_name = logger_name
        
        # Bind correlation_id to all log messages from this instance
        self.logger = self.logger.bind(correlation_id=self.correlation_id)
    
    @classmethod
    def create_logger(cls, repository_name: str) -> "RepositoryLogger":
        """
        Create a logger instance for a specific repository.
        
        Args:
            repository_name: Name of the repository (e.g., "ProductRepo", "MealRepo")
            
        Returns:
            RepositoryLogger instance with repository-specific context
        """
        # Clean up repository name by removing common suffixes
        clean_name = repository_name.lower()
        if clean_name.endswith("repository"):
            clean_name = clean_name[:-10]  # Remove "repository"
        elif clean_name.endswith("repo"):
            clean_name = clean_name[:-4]   # Remove "repo"
        
        logger_name = f"repository.{clean_name}"
        return cls(logger_name)
    
    def with_correlation_id(self, correlation_id: str) -> "RepositoryLogger":
        """
        Create a new logger instance with a specific correlation ID.
        
        Args:
            correlation_id: Correlation ID to use for tracking
            
        Returns:
            New RepositoryLogger instance with the specified correlation ID
        """
        return RepositoryLogger(self.logger_name, correlation_id)
    
    @asynccontextmanager
    async def track_query(
        self, 
        operation: str, 
        **context: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Context manager for tracking query execution time and context.
        
        Args:
            operation: Operation being performed (e.g., "query", "save", "delete")
            **context: Additional context to include in logging
            
        Yields:
            Dictionary that can be updated with additional context during execution
        """
        start_time = time.perf_counter()
        operation_context: Dict[str, Any] = {
            "operation": operation,
            "start_time": datetime.now(timezone.utc).isoformat(),
            **context
        }
        
        # Set correlation ID in context for this operation
        token = correlation_id_ctx.set(self.correlation_id)
        
        try:
            self.logger.debug(
                "Repository operation started",
                operation=operation,
                **context
            )
            
            yield operation_context
            
            # Calculate execution time
            execution_time = time.perf_counter() - start_time
            operation_context["execution_time"] = execution_time
            
            self.logger.info(
                "Repository operation completed",
                operation=operation,
                execution_time=execution_time,
                **context
            )
            
            # Check for performance warnings
            self._check_performance_warnings(operation, execution_time, operation_context)
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            self.logger.error(
                "Repository operation failed",
                operation=operation,
                execution_time=execution_time,
                error=str(e),
                error_type=type(e).__name__,
                **context
            )
            raise
        finally:
            # Reset correlation ID context
            correlation_id_ctx.reset(token)
    
    def log_filter(
        self, 
        filter_key: str, 
        filter_value: Any, 
        filter_type: str,
        column_name: Optional[str] = None
    ) -> None:
        """
        Log filter application with context.
        
        Args:
            filter_key: The filter key being applied (e.g., "name", "created_at_gte")
            filter_value: The filter value
            filter_type: Type of filter operation (e.g., "equals", "greater_than", "in")
            column_name: Database column being filtered (if different from filter_key)
        """
        self.logger.debug(
            "Filter applied",
            filter_key=filter_key,
            filter_value=filter_value,
            filter_type=filter_type,
            column_name=column_name or filter_key,
            value_type=type(filter_value).__name__
        )
    
    def log_join(
        self, 
        join_target: str, 
        join_condition: str,
        join_type: str = "inner"
    ) -> None:
        """
        Log table join operations.
        
        Args:
            join_target: Target table/model being joined
            join_condition: Join condition (e.g., "Product.id = OrderItem.product_id")
            join_type: Type of join (inner, left, right, outer)
        """
        self.logger.debug(
            "Table join applied",
            join_target=join_target,
            join_condition=join_condition,
            join_type=join_type
        )
    
    def log_performance(
        self, 
        query_time: float, 
        result_count: int, 
        memory_usage: Optional[float] = None,
        sql_query: Optional[str] = None
    ) -> None:
        """
        Log performance metrics for repository operations.
        
        Args:
            query_time: Query execution time in seconds
            result_count: Number of results returned
            memory_usage: Memory usage in MB (if available)
            sql_query: SQL query that was executed (for debugging)
        """
        performance_data = {
            "query_time": query_time,
            "result_count": result_count,
            "results_per_second": result_count / query_time if query_time > 0 else 0
        }
        
        if memory_usage is not None:
            performance_data["memory_usage_mb"] = memory_usage
        
        if sql_query:
            performance_data["sql_query"] = sql_query
        
        # Log at appropriate level based on performance
        if query_time > 1.0:  # Slow query warning
            self.logger.warning(
                "Slow query detected",
                **performance_data
            )
        elif result_count > 1000:  # Large result set warning
            self.logger.warning(
                "Large result set returned",
                **performance_data
            )
        else:
            self.logger.debug(
                "Query performance metrics",
                **performance_data
            )
    
    def log_sql_construction(
        self,
        step: str,
        sql_fragment: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create debug logging for SQL query construction steps.
        
        Args:
            step: Construction step (e.g., "select", "where", "join", "order_by")
            sql_fragment: SQL fragment being constructed
            parameters: Parameter bindings (if any)
        """
        log_data: Dict[str, Any] = {
            "sql_construction_step": step,
            "sql_fragment": sql_fragment
        }
        
        if parameters:
            log_data["parameters"] = parameters
        
        self.logger.debug(
            "SQL query construction",
            **log_data
        )
    
    def warn_performance_issue(
        self,
        issue_type: str,
        message: str,
        **context: Any
    ) -> None:
        """
        Log performance warning with context.
        
        Args:
            issue_type: Type of performance issue
            message: Descriptive message about the issue
            **context: Additional context for the warning
        """
        self.logger.warning(
            f"Performance issue detected: {message}",
            issue_type=issue_type,
            **context
        )
    
    def _check_performance_warnings(
        self,
        operation: str,
        execution_time: float,
        context: Dict[str, Any]
    ) -> None:
        """
        Check for potential performance issues and log warnings.
        
        Args:
            operation: Operation that was performed
            execution_time: Time taken for the operation
            context: Operation context
        """
        # Slow query warning
        if execution_time > 1.0:
            self.warn_performance_issue(
                "slow_query",
                f"Query took {execution_time:.2f} seconds",
                operation=operation,
                execution_time=execution_time
            )
        
        # Large result set warning
        result_count = context.get("result_count")
        if result_count and result_count > 1000:
            self.warn_performance_issue(
                "large_result_set",
                f"Query returned {result_count} results",
                operation=operation,
                result_count=result_count
            )
        
        # Complex join warning
        join_count = context.get("join_count")
        if join_count and join_count > 3:
            self.warn_performance_issue(
                "complex_joins",
                f"Query uses {join_count} table joins",
                operation=operation,
                join_count=join_count
            )
        
        # Memory usage warning (if available)
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                if memory_mb > 500:  # > 500MB
                    self.warn_performance_issue(
                        "high_memory_usage",
                        f"High memory usage: {memory_mb:.1f}MB",
                        operation=operation,
                        memory_usage_mb=memory_mb
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass  # Ignore psutil errors
    
    def get_memory_usage(self) -> Optional[float]:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in MB or None if psutil is not available
        """
        if not PSUTIL_AVAILABLE:
            return None
        
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None


def create_repository_logger(repository_name: str) -> RepositoryLogger:
    """
    Convenience function to create a repository logger.
    
    Args:
        repository_name: Name of the repository
        
    Returns:
        Configured RepositoryLogger instance
    """
    return RepositoryLogger.create_logger(repository_name) 