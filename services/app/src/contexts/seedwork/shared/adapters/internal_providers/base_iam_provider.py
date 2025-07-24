import time
from typing import TypeVar, Generic, Type, Dict, Any

import src.contexts.iam.core.endpoints.internal.get as iam_api
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.api_seed_user import ApiSeedUser
from src.logging.logger import logger

# Type variable for the specific ApiUser implementation
TApiUser = TypeVar('TApiUser', bound=ApiSeedUser)


class BaseIAMProvider(Generic[TApiUser]):
    """
    Base class for IAM providers that abstracts common logic across different contexts.
    
    This class eliminates code duplication by providing a generic implementation that
    can be parameterized with context-specific ApiUser types and caller contexts.
    
    Type Parameters:
        TApiUser: The specific ApiUser implementation for the context (must extend ApiSeedUser)
    
    Usage:
        class ProductsIAMProvider(BaseIAMProvider[ApiUser]):
            def __init__(self):
                super().__init__(
                    api_user_class=ApiUser,
                    caller_context="products_catalog"
                )
    """
    
    def __init__(self, api_user_class: Type[TApiUser], caller_context: str):
        """
        Initialize the IAM provider with context-specific configuration.
        
        Args:
            api_user_class: The specific ApiUser class for this context
            caller_context: The context name to pass to the IAM API
        """
        self.api_user_class = api_user_class
        self.caller_context = caller_context
    
    async def get(self, id: str) -> Dict[str, Any]:
        """
        Get user information from the IAM service.
        
        Args:
            id: The user ID to retrieve
            
        Returns:
            Dict containing either:
            - Success: {"statusCode": 200, "body": User domain object}
            - Error: {"statusCode": <error_code>, "body": <error_message>}
            
        Raises:
            Exception: If an unexpected error occurs during the IAM call
        """
        start_time = time.time()
        logger.info(f"BaseIAMProvider.get() called for user_id: {id}, context: {self.caller_context}")
        
        try:
            logger.debug(f"Calling internal IAM API with caller_context='{self.caller_context}' for user: {id}")
            response = await iam_api.get(id=id, caller_context=self.caller_context)
            
            elapsed_time = time.time() - start_time
            logger.debug(f"Internal IAM API response received in {elapsed_time:.3f}s - Status: {response.get('statusCode')}, User: {id}")
            
            if response.get("statusCode") != 200:
                logger.warning(f"IAM API returned non-200 status for user {id}: {response.get('statusCode')} - Body: {response.get('body')}")
                return response
            
            logger.debug(f"Converting IAM response to domain user object for user: {id}")
            response_body = response["body"]
            if not isinstance(response_body, str):
                logger.error(f"Unexpected response body type for user {id}: {type(response_body)} - Expected string")
                raise ValueError(f"Invalid response body type: {type(response_body)}")
            
            user = self.api_user_class.model_validate_json(response_body).to_domain()
            
            logger.debug(f"User from IAMProvider - ID: {user.id}, Roles count: {len(user.roles) if user.roles else 0}")
            logger.info(f"BaseIAMProvider.get() completed successfully for user: {id} in {elapsed_time:.3f}s, context: {self.caller_context}")
            
            return {"statusCode": 200, "body": user}
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"BaseIAMProvider.get() failed for user {id} after {elapsed_time:.3f}s - Error: {type(e).__name__}: {str(e)}, context: {self.caller_context}")
            raise 