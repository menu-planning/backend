"""
Event Publisher for Client Onboarding Context

Publishes domain events to downstream systems using AWS Lambda async invocation
or other async messaging patterns for fire-and-forget semantics.

Dependencies:
- aioboto3: Required for async AWS operations (pip install aioboto3)

The system automatically selects the appropriate implementation:
1. AsyncLambdaEventPublisher/AsyncSNSEventPublisher (production with aioboto3)
2. LocalEventPublisher (development/testing or when AWS not available)
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from enum import Enum

import anyio

from src.config.api_config import api_settings

# AWS dependencies - required for async operations
try:
    import aioboto3  # type: ignore[import-untyped]
    from botocore.exceptions import ClientError  # type: ignore[misc]
    AIOBOTO3_AVAILABLE = True
except ImportError:
    AIOBOTO3_AVAILABLE = False
    # Create placeholder for type checking
    aioboto3 = None  # type: ignore
    ClientError = Exception

from src.contexts.seedwork.shared.domain.event import Event

logger = logging.getLogger(__name__)

# Timeout configuration matching messagebus pattern
TIMEOUT = api_settings.timeout


class PublisherType(Enum):
    """Types of event publishers available."""
    LAMBDA_ASYNC = "lambda_async"
    SNS = "sns"
    LOCAL = "local"


class EventPublisher(ABC):
    """Abstract base class for event publishing."""
    
    @abstractmethod
    async def publish(self, event: Event, target: str) -> bool:
        """
        Publish an event to a target system.
        
        Args:
            event: The domain event to publish
            target: Target identifier (Lambda function name, SNS topic, etc.)
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        pass


class LocalEventPublisher(EventPublisher):
    """
    Local event publisher for development/testing.
    
    Just logs events instead of actually publishing them.
    """
    
    async def publish(self, event: Event, target: str) -> bool:
        """Log event locally instead of publishing."""
        logger.info(
            f"LOCAL EVENT: {event.__class__.__name__} -> {target} "
            f"with data: {event.__dict__}"
        )
        return True


class EventPublisherFactory:
    """Factory for creating appropriate event publishers."""
    
    @staticmethod
    def create(publisher_type: PublisherType = PublisherType.LAMBDA_ASYNC) -> EventPublisher:
        """
        Create an event publisher based on environment and configuration.
        
        Uses aioboto3-based async implementations for production,
        falls back to local publisher for development environments.
        
        Args:
            publisher_type: Type of publisher to create
            
        Returns:
            EventPublisher: Configured publisher instance
        """
        environment = os.getenv("APP_ENVIRONMENT", "production")
        
        # Use local publisher for development environments
        if environment in ["local", "development", "test"]:
            return LocalEventPublisher()
        
        # Use aioboto3 implementations for production if available
        if not AIOBOTO3_AVAILABLE:
            logger.warning("aioboto3 not available, falling back to LocalEventPublisher")
            return LocalEventPublisher()
            
        if publisher_type == PublisherType.LAMBDA_ASYNC:
            return AsyncLambdaEventPublisher()
        elif publisher_type == PublisherType.SNS:
            return AsyncSNSEventPublisher()
        else:
            return LocalEventPublisher()


# Service factory function for dependency injection
def create_event_publisher() -> EventPublisher:
    """Create event publisher based on environment configuration."""
    return EventPublisherFactory.create(PublisherType.LAMBDA_ASYNC)


# Event routing configuration
class EventRoutes:
    """
    Configuration for event routing to specific targets.
    
    Maps event types to their target Lambda functions or topics.
    """
    
    # Example routes - adjust based on your actual Lambda function names
    ROUTES: Dict[str, str] = {
        "OnboardingFormWebhookSetup": "client-onboarding-webhook-setup-handler",
        "FormResponseReceived": "client-onboarding-response-processor", 
        "ClientDataExtracted": "recipes-catalog-client-data-handler",
    }
    
    @classmethod
    def get_target(cls, event_type: str) -> Optional[str]:
        """Get target for an event type."""
        return cls.ROUTES.get(event_type)
    
    @classmethod
    def add_route(cls, event_type: str, target: str):
        """Add a new event route."""
        cls.ROUTES[event_type] = target


class RoutedEventPublisher:
    """
    High-level event publisher that automatically routes events to targets.
    
    Uses EventRoutes to determine where each event type should be sent.
    Enhanced with anyio for structured concurrency, timeout handling, and batch operations.
    """
    
    def __init__(self, publisher: EventPublisher):
        self.publisher = publisher
    
    async def publish_event(self, event: Event, timeout: int = TIMEOUT) -> bool:
        """
        Publish an event using automatic routing with timeout support.
        
        Args:
            event: Domain event to publish
            timeout: Maximum time to wait for publishing (seconds)
            
        Returns:
            bool: True if published successfully, False if no route or error
        """
        event_type = event.__class__.__name__
        target = EventRoutes.get_target(event_type)
        
        if not target:
            logger.warning(f"No route configured for event type: {event_type}")
            return False
        
        # Use anyio timeout like messagebus
        with anyio.move_on_after(timeout) as scope:
            try:
                return await self.publisher.publish(event, target)
            except Exception as e:
                logger.error(f"Exception publishing event {event}: {e}")
                return False
        
        if scope.cancel_called:
            logger.error(f"Timeout publishing event {event} after {timeout}s")
            return False
        
        return True
    
    async def publish_to_target(self, event: Event, target: str, timeout: int = TIMEOUT) -> bool:
        """
        Publish an event to a specific target, bypassing routing with timeout support.
        
        Args:
            event: Domain event to publish
            target: Specific target to publish to
            timeout: Maximum time to wait for publishing (seconds)
            
        Returns:
            bool: True if published successfully, False on error
        """
        with anyio.move_on_after(timeout) as scope:
            try:
                return await self.publisher.publish(event, target)
            except Exception as e:
                logger.error(f"Exception publishing event {event} to {target}: {e}")
                return False
        
        if scope.cancel_called:
            logger.error(f"Timeout publishing event {event} to {target} after {timeout}s")
            return False
        
        return True
    
    async def publish_events_batch(self, events: List[Event], timeout: int = TIMEOUT) -> List[bool]:
        """
        Publish multiple events concurrently using anyio task groups.
        
        Uses structured concurrency to publish all events in parallel,
        following the same pattern as messagebus event handling.
        
        Args:
            events: List of domain events to publish
            timeout: Maximum time to wait for all publishing operations
            
        Returns:
            List[bool]: Results for each event (True if published successfully)
        """
        if not events:
            return []
        
        results = [False] * len(events)
        
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    for i, event in enumerate(events):
                        tg.start_soon(self._publish_single_with_result, event, results, i)
            except Exception as e:
                logger.error(f"Exception in batch publishing: {e}")
        
        if scope.cancel_called:
            logger.error(f"Timeout in batch publishing after {timeout}s")
        
        return results
    
    async def _publish_single_with_result(self, event: Event, results: List[bool], index: int):
        """Helper method for batch publishing that stores results."""
        try:
            result = await self.publish_event(event, timeout=TIMEOUT // 2)  # Shorter timeout for individual events
            results[index] = result
            if result:
                logger.debug(f"Successfully published event {event.__class__.__name__} in batch")
            else:
                logger.warning(f"Failed to publish event {event.__class__.__name__} in batch")
        except Exception as e:
            logger.error(f"Exception publishing event {event} in batch: {e}")
            results[index] = False
    
    async def publish_events_to_targets(self, event_target_pairs: List[tuple[Event, str]], timeout: int = TIMEOUT) -> List[bool]:
        """
        Publish multiple events to specific targets concurrently.
        
        Args:
            event_target_pairs: List of (event, target) tuples
            timeout: Maximum time to wait for all publishing operations
            
        Returns:
            List[bool]: Results for each event-target pair
        """
        if not event_target_pairs:
            return []
        
        results = [False] * len(event_target_pairs)
        
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    for i, (event, target) in enumerate(event_target_pairs):
                        tg.start_soon(self._publish_to_target_with_result, event, target, results, i)
            except Exception as e:
                logger.error(f"Exception in batch target publishing: {e}")
        
        if scope.cancel_called:
            logger.error(f"Timeout in batch target publishing after {timeout}s")
        
        return results
    
    async def _publish_to_target_with_result(self, event: Event, target: str, results: List[bool], index: int):
        """Helper method for batch target publishing that stores results."""
        try:
            result = await self.publish_to_target(event, target, timeout=TIMEOUT // 2)
            results[index] = result
            if result:
                logger.debug(f"Successfully published event {event.__class__.__name__} to {target} in batch")
            else:
                logger.warning(f"Failed to publish event {event.__class__.__name__} to {target} in batch")
        except Exception as e:
            logger.error(f"Exception publishing event {event} to {target} in batch: {e}")
            results[index] = False 


# Factory for the routed publisher
def create_routed_event_publisher() -> RoutedEventPublisher:
    """Create a routed event publisher with default configuration."""
    base_publisher = create_event_publisher()
    return RoutedEventPublisher(base_publisher)


class AsyncLambdaEventPublisher(EventPublisher):
    """
    Truly async Lambda event publisher using aioboto3.
    
    Provides proper async/await support without blocking the event loop.
    This is the preferred implementation when aioboto3 is available.
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        if not AIOBOTO3_AVAILABLE:
            raise ImportError("aioboto3 is required for AsyncLambdaEventPublisher")
        self.session = aioboto3.Session()  # type: ignore[union-attr]
        self.region_name = region_name
    
    async def publish(self, event: Event, target: str) -> bool:
        """
        Invoke a Lambda function asynchronously with the event payload.
        
        Args:
            event: Domain event to publish
            target: Lambda function name or ARN
            
        Returns:
            bool: True if invocation was accepted, False on error
        """
        async with self.session.client('lambda', region_name=self.region_name) as lambda_client:  # type: ignore[union-attr]
            try:
                # Convert event to Lambda payload
                payload = {
                    "eventType": event.__class__.__name__,
                    "eventData": event.__dict__,
                    "source": "client_onboarding",
                }
                
                # True async invocation using aioboto3
                response = await lambda_client.invoke(
                    FunctionName=target,
                    InvocationType='Event',  # Async invocation
                    Payload=json.dumps(payload)
                )
                
                # Check if invocation was accepted
                status_code = response.get('StatusCode', 0)
                if status_code == 202:  # Accepted for async processing
                    logger.info(f"Event {event.__class__.__name__} published to Lambda {target}")
                    return True
                else:
                    logger.warning(f"Lambda invocation returned status {status_code} for {target}")
                    return False
                    
            except ClientError as e:
                logger.error(f"Failed to publish event to Lambda {target}: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error publishing to Lambda {target}: {e}")
                return False


class AsyncSNSEventPublisher(EventPublisher):
    """
    Truly async SNS event publisher using aioboto3.
    
    Provides proper async/await support without blocking the event loop.
    This is the preferred implementation when aioboto3 is available.
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        if not AIOBOTO3_AVAILABLE:
            raise ImportError("aioboto3 is required for AsyncSNSEventPublisher")
        self.session = aioboto3.Session()  # type: ignore[union-attr]
        self.region_name = region_name
    
    async def publish(self, event: Event, target: str) -> bool:
        """
        Publish event to an SNS topic.
        
        Args:
            event: Domain event to publish
            target: SNS topic ARN
            
        Returns:
            bool: True if published successfully, False on error
        """
        async with self.session.client('sns', region_name=self.region_name) as sns_client:  # type: ignore[union-attr]
            try:
                message = {
                    "eventType": event.__class__.__name__,
                    "eventData": event.__dict__,
                    "source": "client_onboarding"
                }
                
                # True async publish using aioboto3
                response = await sns_client.publish(
                    TopicArn=target,
                    Message=json.dumps(message),
                    Subject=f"ClientOnboarding: {event.__class__.__name__}"
                )
                
                if response.get('MessageId'):
                    logger.info(f"Event {event.__class__.__name__} published to SNS {target}")
                    return True
                else:
                    logger.warning(f"SNS publish failed for topic {target}")
                    return False
                    
            except ClientError as e:
                logger.error(f"Failed to publish event to SNS {target}: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error publishing to SNS {target}: {e}")
                return False 