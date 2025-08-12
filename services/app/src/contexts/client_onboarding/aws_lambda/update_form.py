"""
Update Form Lambda Handler

Lambda endpoint for updating existing onboarding forms with proper authorization and validation.
"""

from typing import Any, Dict
import anyio
from datetime import UTC, datetime

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_update_webhook_url import (
    ApiUpdateWebhookUrl,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_management import (
    FormManagementResponse, FormOperationType,
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
from src.contexts.client_onboarding.core.adapters.external_providers.iam.iam_provider_api_for_client_onboarding import IAMProvider

from .CORS_headers import CORS_headers

container = Container()
logging_middleware = create_api_logging_middleware()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler to update an existing onboarding form.
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        logger.debug(f"Update form event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
        
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
        
        # Parse and validate request body (new webhook URL)
        try:
            raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
            if not isinstance(raw_body, str) or not raw_body.strip():
                raw_body = "{}"
            api_cmd = ApiUpdateWebhookUrl.model_validate_json(raw_body)
            # Ensure path form_id overrides body form_id
            api_cmd = ApiUpdateWebhookUrl(form_id=form_id, new_webhook_url=api_cmd.new_webhook_url)
            logger.debug("Parsed update webhook URL command")
        except Exception as e:
            logger.warning(f"Invalid update form request body: {e}")
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": '{"message": "Invalid request body"}',
            }

        # Business logic: Update form through UoW
        bus: MessageBus = container.bootstrap()
        
        try:
            uow: UnitOfWork
            async with bus.uow as uow:
                logger.debug(f"Updating form {form_id} for user {current_user.id}")
                
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
                
                # Update form fields
                updated_fields = []
                if api_cmd.new_webhook_url is not None:
                    existing_form.webhook_url = str(api_cmd.new_webhook_url)
                    updated_fields.append("webhook_url")
                
                # Status updates are not part of the API command in this endpoint
                
                existing_form.updated_at = datetime.now(UTC)
                updated_fields.append("updated_at")
                
                await uow.commit()
                
                # Create success response
                response = FormManagementResponse(
                    success=True,
                    operation=FormOperationType.UPDATE,
                    form_id=form_id,
                    message=f"Form {form_id} updated successfully",
                    created_form_id=None,
                    updated_fields=updated_fields,
                    webhook_status="updated",
                    operation_timestamp=datetime.now(UTC),
                    execution_time_ms=None,
                    error_code=None,
                    error_details=None,
                    warnings=[]
                )
                
                logger.info(f"Successfully updated form {form_id} for user {current_user.id}")
                
        except Exception as e:
            logger.error(f"Failed to update form: {e}")
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": '{"message": "Internal server error during form update"}',
            }

        # Serialize response
        try:
            response_body = response.model_dump_json()
            logger.debug(f"Successfully updated form and returning response")
        except Exception as e:
            logger.error(f"Failed to serialize form update response: {str(e)}")
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
    """Lambda function handler entry point for updating forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context) 