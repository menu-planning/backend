"""
Create Form Lambda Handler

Lambda endpoint for creating new onboarding forms with proper authorization and validation.
"""

from typing import Any, Dict
import anyio
from datetime import UTC, datetime
from pydantic import ValidationError

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.api_schemas.commands.form_management_commands import (
    CreateFormCommand, FormManagementResponse, FormOperationType
)
from src.contexts.client_onboarding.core.adapters.middleware.auth_middleware import (
    ClientOnboardingAuthContext
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
    Lambda function handler to create a new onboarding form.
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        logger.debug(f"Create form event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
        
        # Validate user authentication and get user object
        auth_result = await LambdaHelpers.validate_user_authentication(
            event, CORS_headers, IAMProvider, return_user_object=True, mock_user_class=SeedUser
        )
        if isinstance(auth_result, dict):
            return auth_result  # Return error response
        _, current_user = auth_result
        
        # Create auth context for permission checking
        auth_context = ClientOnboardingAuthContext(
            user_id=current_user.id,
            user_object=current_user,
            is_authenticated=True
        )
        
        # Parse and validate request body
        try:
            body = LambdaHelpers.extract_request_body(event, parse_json=True)
            create_command = CreateFormCommand.model_validate(body)
            logger.debug(f"Parsed create form command: {create_command}")
        except ValidationError as e:
            logger.warning(f"Invalid create form request body: {e}")
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": f'{{"message": "Invalid request body", "errors": {e.errors()}}}',
            }
        except Exception as e:
            logger.error(f"Failed to parse request body: {e}")
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": '{"message": "Invalid request body format"}',
            }

        # Business logic: Create form through UoW
        bus: MessageBus = container.bootstrap()
        
        try:
            uow: UnitOfWork
            async with bus.uow as uow:
                logger.debug(f"Creating form for user {current_user.id} with TypeForm ID: {create_command.typeform_id}")
                
                # Check if form with this TypeForm ID already exists
                existing_form = await uow.onboarding_forms.get_by_typeform_id(create_command.typeform_id)
                if existing_form and existing_form.user_id == current_user.id:
                    return {
                        "statusCode": 409,
                        "headers": CORS_headers,
                        "body": '{"message": "Form with this TypeForm ID already exists for this user"}',
                    }
                
                # Create new form
                from src.contexts.client_onboarding.models.onboarding_form import (
                    OnboardingForm, OnboardingFormStatus
                )
                
                new_form = OnboardingForm(
                    user_id=current_user.id,
                    typeform_id=create_command.typeform_id,
                    webhook_url=str(create_command.webhook_url),
                    status=OnboardingFormStatus.ACTIVE if create_command.auto_activate else OnboardingFormStatus.DRAFT,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                
                await uow.onboarding_forms.add(new_form)
                await uow.commit()
                
                # Create success response
                response = FormManagementResponse(
                    success=True,
                    operation=FormOperationType.CREATE,
                    form_id=new_form.id,
                    message=f"Form created successfully with ID {new_form.id}",
                    created_form_id=new_form.id,
                    updated_fields=[],
                    webhook_status="pending",
                    operation_timestamp=datetime.now(UTC),
                    execution_time_ms=None,
                    error_code=None,
                    error_details=None,
                    warnings=[]
                )
                
                logger.info(f"Successfully created form {new_form.id} for user {current_user.id}")
                
        except Exception as e:
            logger.error(f"Failed to create form: {e}")
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": '{"message": "Internal server error during form creation"}',
            }

        # Serialize response
        try:
            response_body = response.model_dump_json()
            logger.debug(f"Successfully created form and returning response")
        except Exception as e:
            logger.error(f"Failed to serialize form creation response: {str(e)}")
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": '{"message": "Internal server error during response serialization"}',
            }

        return {
            "statusCode": 201,
            "headers": CORS_headers,
            "body": response_body,
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler entry point for creating forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context) 