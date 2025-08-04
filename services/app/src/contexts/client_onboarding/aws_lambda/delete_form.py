"""
Delete Form Lambda Handler

Lambda endpoint for deleting onboarding forms with proper authorization and validation.
"""

from typing import Any, Dict
import anyio
from datetime import UTC, datetime

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.form_management_commands import (
    FormManagementResponse, FormOperationType
)

from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_api_logging_middleware
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id
from src.contexts.client_onboarding.core.adapters.internal_providers.iam.iam_provider_api_for_client_onboarding import IAMProvider

from .CORS_headers import CORS_headers

container = Container()
logging_middleware = create_api_logging_middleware()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler to delete an onboarding form.
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        logger.debug(f"Delete form event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
        
        # Validate user authentication and get user object
        auth_result = await LambdaHelpers.validate_user_authentication(
            event, CORS_headers, IAMProvider, return_user_object=True, mock_user_class=SeedUser
        )
        if isinstance(auth_result, dict):
            return auth_result  # Return error response
        _, current_user = auth_result
        
        # Get form ID from path parameters
        form_id = event.get("pathParameters", {}).get("form_id")
        if not form_id:
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": '{"message": "Form ID is required in path parameters"}',
            }
        
        try:
            form_id = int(form_id)
        except ValueError:
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": '{"message": "Invalid form ID format"}',
            }

        # Business logic: Delete form through UoW
        bus: MessageBus = container.bootstrap()
        
        try:
            uow: UnitOfWork
            async with bus.uow as uow:
                logger.debug(f"Deleting form {form_id} for user {current_user.id}")
                
                # Get existing form and verify ownership
                existing_form = await uow.onboarding_forms.get_by_id(form_id)
                if not existing_form:
                    return {
                        "statusCode": 404,
                        "headers": CORS_headers,
                        "body": '{"message": "Form not found"}',
                    }
                
                # Check ownership
                if existing_form.user_id != current_user.id:
                    return {
                        "statusCode": 403,
                        "headers": CORS_headers,
                        "body": '{"message": "Access denied: You do not own this form"}',
                    }
                
                # Soft delete - mark as deleted
                from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingFormStatus
                existing_form.status = OnboardingFormStatus.DELETED
                existing_form.updated_at = datetime.now(UTC)
                
                await uow.commit()
                
                # Create success response
                response = FormManagementResponse(
                    success=True,
                    operation=FormOperationType.DELETE,
                    form_id=form_id,
                    message=f"Form {form_id} deleted successfully",
                    created_form_id=None,
                    updated_fields=["status", "updated_at"],
                    webhook_status="deleted",
                    operation_timestamp=datetime.now(UTC),
                    execution_time_ms=None,
                    error_code=None,
                    error_details=None,
                    warnings=[]
                )
                
                logger.info(f"Successfully deleted form {form_id} for user {current_user.id}")
                
        except Exception as e:
            logger.error(f"Failed to delete form: {e}")
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": '{"message": "Internal server error during form deletion"}',
            }

        # Serialize response
        try:
            response_body = response.model_dump_json()
            logger.debug(f"Successfully deleted form and returning response")
        except Exception as e:
            logger.error(f"Failed to serialize form deletion response: {str(e)}")
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": '{"message": "Internal server error during response serialization"}',
            }

        return {
            "statusCode": 200,
            "headers": CORS_headers,
            "body": response_body,
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler entry point for deleting forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context) 