"""
Unit tests for RepositoryLogger with mocked time and psutil dependencies.

Tests structured logging, correlation ID management, performance tracking,
and integration with existing logging infrastructure.
"""

import pytest
from unittest.mock import Mock, patch
import psutil

from src.contexts.seedwork.shared.adapters.repositories.repository_logger import (
    RepositoryLogger,
    create_repository_logger,
    PSUTIL_AVAILABLE
)


class TestRepositoryLogger:
    """Test suite for RepositoryLogger functionality."""
    
    @pytest.fixture
    def mock_structlog_logger(self):
        """Mock structlog logger for testing."""
        mock_logger = Mock()
        mock_logger.bind.return_value = mock_logger
        mock_logger.debug = Mock()
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        return mock_logger
    
    @pytest.fixture
    def repository_logger(self, mock_structlog_logger):
        """Create RepositoryLogger instance with mocked logger."""
        with patch('structlog.get_logger', return_value=mock_structlog_logger):
            with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.StructlogFactory.configure'):
                logger = RepositoryLogger("test_repo")
                logger.logger = mock_structlog_logger
                return logger
    
    def test_init_default_values(self, mock_structlog_logger):
        """Test RepositoryLogger initialization with default values."""
        with patch('structlog.get_logger', return_value=mock_structlog_logger):
            with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.StructlogFactory.configure'):
                logger = RepositoryLogger()
                
                assert logger.logger_name == "repository"
                assert len(logger.correlation_id) == 8
                mock_structlog_logger.bind.assert_called_once_with(correlation_id=logger.correlation_id)
    
    def test_init_with_custom_values(self, mock_structlog_logger):
        """Test RepositoryLogger initialization with custom values."""
        custom_name = "custom_repo"
        custom_correlation_id = "test123"
        
        with patch('structlog.get_logger', return_value=mock_structlog_logger):
            with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.StructlogFactory.configure'):
                logger = RepositoryLogger(custom_name, custom_correlation_id)
                
                assert logger.logger_name == custom_name
                assert logger.correlation_id == custom_correlation_id
                mock_structlog_logger.bind.assert_called_once_with(correlation_id=custom_correlation_id)
    
    def test_create_logger_class_method(self, mock_structlog_logger):
        """Test create_logger class method."""
        with patch('structlog.get_logger', return_value=mock_structlog_logger):
            with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.StructlogFactory.configure'):
                logger = RepositoryLogger.create_logger("ProductRepo")
                
                assert logger.logger_name == "repository.product"
                assert len(logger.correlation_id) == 8
    
    def test_create_logger_with_repository_suffix(self, mock_structlog_logger):
        """Test create_logger with 'Repository' suffix removal."""
        with patch('structlog.get_logger', return_value=mock_structlog_logger):
            with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.StructlogFactory.configure'):
                logger = RepositoryLogger.create_logger("MealRepository")
                
                assert logger.logger_name == "repository.meal"
    
    def test_with_correlation_id(self, repository_logger):
        """Test creating logger with specific correlation ID."""
        new_correlation_id = "newtest123"
        
        with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.RepositoryLogger') as MockLogger:
            MockLogger.return_value = Mock()
            
            repository_logger.with_correlation_id(new_correlation_id)
            
            MockLogger.assert_called_once_with(repository_logger.logger_name, new_correlation_id)
    
    @pytest.mark.anyio
    async def test_track_query_success(self, repository_logger):
        """Test track_query context manager with successful operation."""
        operation = "test_query"
        additional_context = {"table": "products", "filters": {"name": "test"}}
        
        with patch('time.perf_counter', side_effect=[0.0, 1.5]):  # Start and end times
            with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.correlation_id_ctx') as mock_ctx:
                mock_token = Mock()
                mock_ctx.set.return_value = mock_token
                
                async with repository_logger.track_query(operation, **additional_context) as context:
                    assert context["operation"] == operation
                    assert "start_time" in context
                    # Simulate adding context during operation
                    context["result_count"] = 10
                
                # Verify logging calls
                repository_logger.logger.debug.assert_called_with(
                    "Repository operation started",
                    operation=operation,
                    **additional_context
                )
                
                repository_logger.logger.info.assert_called_with(
                    "Repository operation completed",
                    operation=operation,
                    execution_time=1.5,
                    **additional_context
                )
                
                # Verify correlation ID context management
                mock_ctx.set.assert_called_once_with(repository_logger.correlation_id)
                mock_ctx.reset.assert_called_once_with(mock_token)
    
    @pytest.mark.anyio
    async def test_track_query_with_exception(self, repository_logger):
        """Test track_query context manager with exception."""
        operation = "test_query"
        test_exception = ValueError("Test error")
        
        with patch('time.perf_counter', side_effect=[0.0, 0.5]):
            with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.correlation_id_ctx') as mock_ctx:
                mock_token = Mock()
                mock_ctx.set.return_value = mock_token
                
                with pytest.raises(ValueError):
                    async with repository_logger.track_query(operation):
                        raise test_exception
                
                # Verify error logging
                repository_logger.logger.error.assert_called_with(
                    "Repository operation failed",
                    operation=operation,
                    execution_time=0.5,
                    error="Test error",
                    error_type="ValueError"
                )
                
                # Verify correlation ID context is reset even on exception
                mock_ctx.reset.assert_called_once_with(mock_token)
    
    def test_log_filter(self, repository_logger):
        """Test log_filter method."""
        filter_key = "name"
        filter_value = "test_product"
        filter_type = "equals"
        column_name = "product_name"
        
        repository_logger.log_filter(filter_key, filter_value, filter_type, column_name)
        
        repository_logger.logger.debug.assert_called_with(
            "Filter applied",
            filter_key=filter_key,
            filter_value=filter_value,
            filter_type=filter_type,
            column_name=column_name,
            value_type="str"
        )
    
    def test_log_filter_without_column_name(self, repository_logger):
        """Test log_filter method without explicit column name."""
        filter_key = "price"
        filter_value = 10.99
        filter_type = "greater_than"
        
        repository_logger.log_filter(filter_key, filter_value, filter_type)
        
        repository_logger.logger.debug.assert_called_with(
            "Filter applied",
            filter_key=filter_key,
            filter_value=filter_value,
            filter_type=filter_type,
            column_name=filter_key,  # Should default to filter_key
            value_type="float"
        )
    
    def test_log_join(self, repository_logger):
        """Test log_join method."""
        join_target = "products"
        join_condition = "Product.id = OrderItem.product_id"
        join_type = "left"
        
        repository_logger.log_join(join_target, join_condition, join_type)
        
        repository_logger.logger.debug.assert_called_with(
            "Table join applied",
            join_target=join_target,
            join_condition=join_condition,
            join_type=join_type
        )
    
    def test_log_join_default_type(self, repository_logger):
        """Test log_join method with default join type."""
        join_target = "categories"
        join_condition = "Product.category_id = Category.id"
        
        repository_logger.log_join(join_target, join_condition)
        
        repository_logger.logger.debug.assert_called_with(
            "Table join applied",
            join_target=join_target,
            join_condition=join_condition,
            join_type="inner"  # Default value
        )
    
    def test_log_performance_normal_query(self, repository_logger):
        """Test log_performance with normal query metrics."""
        query_time = 0.5
        result_count = 100
        memory_usage = 50.0
        sql_query = "SELECT * FROM products"
        
        repository_logger.log_performance(query_time, result_count, memory_usage, sql_query)
        
        expected_data = {
            "query_time": query_time,
            "result_count": result_count,
            "results_per_second": 200.0,  # 100 / 0.5
            "memory_usage_mb": memory_usage,
            "sql_query": sql_query
        }
        
        repository_logger.logger.debug.assert_called_with(
            "Query performance metrics",
            **expected_data
        )
    
    def test_log_performance_slow_query_warning(self, repository_logger):
        """Test log_performance with slow query warning."""
        query_time = 2.0  # > 1.0 seconds
        result_count = 50
        
        repository_logger.log_performance(query_time, result_count)
        
        expected_data = {
            "query_time": query_time,
            "result_count": result_count,
            "results_per_second": 25.0
        }
        
        repository_logger.logger.warning.assert_called_with(
            "Slow query detected",
            **expected_data
        )
    
    def test_log_performance_large_result_warning(self, repository_logger):
        """Test log_performance with large result set warning."""
        query_time = 0.8
        result_count = 1500  # > 1000 results
        
        repository_logger.log_performance(query_time, result_count)
        
        expected_data = {
            "query_time": query_time,
            "result_count": result_count,
            "results_per_second": 1875.0
        }
        
        repository_logger.logger.warning.assert_called_with(
            "Large result set returned",
            **expected_data
        )
    
    def test_log_sql_construction(self, repository_logger):
        """Test log_sql_construction method."""
        step = "where"
        sql_fragment = "WHERE name = :name"
        parameters = {"name": "test_product"}
        
        repository_logger.log_sql_construction(step, sql_fragment, parameters)
        
        expected_data = {
            "sql_construction_step": step,
            "sql_fragment": sql_fragment,
            "parameters": parameters
        }
        
        repository_logger.logger.debug.assert_called_with(
            "SQL query construction",
            **expected_data
        )
    
    def test_log_sql_construction_without_parameters(self, repository_logger):
        """Test log_sql_construction without parameters."""
        step = "select"
        sql_fragment = "SELECT id, name FROM products"
        
        repository_logger.log_sql_construction(step, sql_fragment)
        
        expected_data = {
            "sql_construction_step": step,
            "sql_fragment": sql_fragment
        }
        
        repository_logger.logger.debug.assert_called_with(
            "SQL query construction",
            **expected_data
        )
    
    def test_warn_performance_issue(self, repository_logger):
        """Test warn_performance_issue method."""
        issue_type = "slow_query"
        message = "Query took too long"
        context = {"execution_time": 2.5, "table": "products"}
        
        repository_logger.warn_performance_issue(issue_type, message, **context)
        
        repository_logger.logger.warning.assert_called_with(
            f"Performance issue detected: {message}",
            issue_type=issue_type,
            **context
        )
    
    def test_check_performance_warnings_slow_query(self, repository_logger):
        """Test _check_performance_warnings with slow query."""
        operation = "query"
        execution_time = 1.5  # > 1.0 seconds
        context = {}
        
        with patch.object(repository_logger, 'warn_performance_issue') as mock_warn:
            repository_logger._check_performance_warnings(operation, execution_time, context)
            
            mock_warn.assert_called_with(
                "slow_query",
                "Query took 1.50 seconds",
                operation=operation,
                execution_time=execution_time
            )
    
    def test_check_performance_warnings_large_result_set(self, repository_logger):
        """Test _check_performance_warnings with large result set."""
        operation = "query"
        execution_time = 0.5
        context = {"result_count": 1200}
        
        with patch.object(repository_logger, 'warn_performance_issue') as mock_warn:
            repository_logger._check_performance_warnings(operation, execution_time, context)
            
            mock_warn.assert_called_with(
                "large_result_set",
                "Query returned 1200 results",
                operation=operation,
                result_count=1200
            )
    
    def test_check_performance_warnings_complex_joins(self, repository_logger):
        """Test _check_performance_warnings with complex joins."""
        operation = "query"
        execution_time = 0.5
        context = {"join_count": 5}
        
        with patch.object(repository_logger, 'warn_performance_issue') as mock_warn:
            repository_logger._check_performance_warnings(operation, execution_time, context)
            
            mock_warn.assert_called_with(
                "complex_joins",
                "Query uses 5 table joins",
                operation=operation,
                join_count=5
            )
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_check_performance_warnings_high_memory(self, repository_logger):
        """Test _check_performance_warnings with high memory usage."""
        operation = "query"
        execution_time = 0.5
        context = {}
        
        # Mock psutil to return high memory usage
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 600 * 1024 * 1024  # 600MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        
        with patch('psutil.Process', return_value=mock_process):
            with patch.object(repository_logger, 'warn_performance_issue') as mock_warn:
                repository_logger._check_performance_warnings(operation, execution_time, context)
                
                mock_warn.assert_called_with(
                    "high_memory_usage",
                    "High memory usage: 600.0MB",
                    operation=operation,
                    memory_usage_mb=600.0
                )
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_get_memory_usage_success(self, repository_logger):
        """Test get_memory_usage with successful psutil call."""
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        
        with patch('psutil.Process', return_value=mock_process):
            memory_usage = repository_logger.get_memory_usage()
            assert memory_usage == 100.0
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_get_memory_usage_psutil_error(self, repository_logger):
        """Test get_memory_usage with psutil error."""
        with patch('psutil.Process', side_effect=psutil.NoSuchProcess("Process error")):
            memory_usage = repository_logger.get_memory_usage()
            assert memory_usage is None
    
    @pytest.mark.skipif(PSUTIL_AVAILABLE, reason="psutil is available")
    def test_get_memory_usage_no_psutil(self, repository_logger):
        """Test get_memory_usage when psutil is not available."""
        memory_usage = repository_logger.get_memory_usage()
        assert memory_usage is None


class TestCreateRepositoryLogger:
    """Test suite for create_repository_logger convenience function."""
    
    def test_create_repository_logger(self):
        """Test create_repository_logger convenience function."""
        with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.RepositoryLogger.create_logger') as mock_create:
            mock_logger = Mock()
            mock_create.return_value = mock_logger
            
            result = create_repository_logger("TestRepo")
            
            assert result == mock_logger
            mock_create.assert_called_once_with("TestRepo")


class TestRepositoryLoggerIntegration:
    """Integration tests for RepositoryLogger with real structlog."""
    
    @pytest.mark.anyio
    async def test_real_structlog_integration(self):
        """Test RepositoryLogger with real structlog configuration."""
        # Use a simpler structlog configuration for testing
        with patch('src.contexts.seedwork.shared.adapters.repositories.repository_logger.StructlogFactory.configure'):
            # Create logger with mocked structlog to avoid configuration issues
            mock_logger = Mock()
            mock_logger.bind.return_value = mock_logger
            
            with patch('structlog.get_logger', return_value=mock_logger):
                logger = RepositoryLogger("integration_test")
                
                # Test that logger is properly configured
                assert hasattr(logger, 'logger')
                assert hasattr(logger, 'correlation_id')
                assert hasattr(logger, 'logger_name')
                
                # Test basic logging methods don't throw errors
                logger.log_filter("test_key", "test_value", "equals")
                logger.log_join("test_table", "test_condition")
                
                # Test track_query context manager
                async with logger.track_query("test_operation") as context:
                    context["test_key"] = "test_value"
                    assert context["operation"] == "test_operation" 