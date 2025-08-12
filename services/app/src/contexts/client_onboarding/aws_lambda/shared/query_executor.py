"""
Shared query execution logic for response query Lambda handlers.

Contains the core business logic for executing different types of response queries
that can be reused across multiple Lambda functions.
"""

from pydantic import ValidationError

from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import (
    QueryType, ResponseQueryRequest, ResponseQueryResponse, FormSummary, ResponseSummary
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.client_identifiers import ClientIdentifierSet
from src.contexts.client_onboarding.core.adapters.validators.ownership_validator import (
    FormOwnershipValidator, OwnershipValidationRequest
)
from src.logging.logger import logger


async def execute_query(query: ResponseQueryRequest, uow: UnitOfWork, ownership_validator: FormOwnershipValidator) -> ResponseQueryResponse:
    """Execute a single query operation."""
    try:
        if query.query_type == QueryType.FORMS_BY_USER:
            # Get all forms for the user
            forms = await uow.onboarding_forms.get_by_user_id(query.user_id)
            
            form_summaries = []
            for form in forms:
                # Get response count for each form
                responses = await uow.form_responses.get_by_form_id(form.id)
                form_summary = FormSummary(
                    id=form.id,
                    typeform_id=form.typeform_id,
                    title=form.typeform_id,  # Use typeform_id as title since no title field exists
                    status=form.status.value,
                    created_at=form.created_at,
                    updated_at=form.updated_at,
                    response_count=len(responses)
                )
                form_summaries.append(form_summary)
            
            # Apply pagination
            total_count = len(form_summaries)
            start_idx = query.offset if query.offset is not None else 0
            end_idx = start_idx + (query.limit if query.limit is not None else 50)
            paginated_forms = form_summaries[start_idx:end_idx]
            
            return ResponseQueryResponse(
                success=True,
                query_type=query.query_type,
                total_count=total_count,
                returned_count=len(paginated_forms),
                forms=paginated_forms,
                responses=None,
                pagination={
                    "offset": query.offset,
                    "limit": query.limit,
                    "has_more": end_idx < total_count
                }
            )
            
        elif query.query_type == QueryType.RESPONSES_BY_FORM:
            if query.form_id is None:
                return ResponseQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    total_count=0,
                    returned_count=0,
                    forms=None,
                    responses=None,
                    pagination=None
                )
            
            # Validate form ownership
            form = await uow.onboarding_forms.get_by_id(query.form_id)
            if not form:
                return ResponseQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    total_count=0,
                    returned_count=0,
                    forms=None,
                    responses=None,
                    pagination=None
                )
            
            # Check ownership using the correct validator interface
            validation_request = OwnershipValidationRequest(
                user_id=query.user_id,
                form_id=form.typeform_id,
                onboarding_form_id=None,
                operation="query_responses"
            )
            validation_result = await ownership_validator.validate_form_access(validation_request, uow)
            if not validation_result.is_valid:
                return ResponseQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    total_count=0,
                    returned_count=0,
                    forms=None,
                    responses=None,
                    pagination=None
                )
            
            # Get responses for the form
            responses = await uow.form_responses.get_by_form_id(query.form_id)
            
            response_summaries = []
            for response in responses:
                # Parse client identifiers if available
                client_identifiers = None
                if response.client_identifiers:
                    try:
                        client_identifiers = ClientIdentifierSet.model_validate(response.client_identifiers)
                    except ValidationError:
                        pass
                
                # Only include full data for small queries
                include_full_data = (query.limit is not None and query.limit <= 10)
                response_summary = ResponseSummary(
                    id=response.id,
                    response_id=response.response_id,
                    form_id=response.form_id,
                    client_identifiers=client_identifiers,
                    submitted_at=response.submitted_at,
                    processed_at=response.processed_at,
                    response_data=response.response_data if include_full_data else None
                )
                response_summaries.append(response_summary)
            
            # Apply pagination
            total_count = len(response_summaries)
            start_idx = query.offset if query.offset is not None else 0
            end_idx = start_idx + (query.limit if query.limit is not None else 50)
            paginated_responses = response_summaries[start_idx:end_idx]
            
            return ResponseQueryResponse(
                success=True,
                query_type=query.query_type,
                total_count=total_count,
                returned_count=len(paginated_responses),
                forms=None,
                responses=paginated_responses,
                pagination={
                    "offset": query.offset,
                    "limit": query.limit,
                    "has_more": end_idx < total_count
                }
            )
            
        elif query.query_type == QueryType.RESPONSE_BY_ID:
            if query.response_id is None:
                return ResponseQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    total_count=0,
                    returned_count=0,
                    forms=None,
                    responses=None,
                    pagination=None
                )
            
            # Get specific response
            response = await uow.form_responses.get_by_response_id(query.response_id)
            if not response:
                return ResponseQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    total_count=0,
                    returned_count=0,
                    forms=None,
                    responses=None,
                    pagination=None
                )
            
            # Validate form ownership
            form = await uow.onboarding_forms.get_by_id(response.form_id)
            if not form:
                return ResponseQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    total_count=0,
                    returned_count=0,
                    forms=None,
                    responses=None,
                    pagination=None
                )
            
            validation_request = OwnershipValidationRequest(
                user_id=query.user_id,
                form_id=form.typeform_id,
                onboarding_form_id=None,
                operation="query_response_by_id"
            )
            validation_result = await ownership_validator.validate_form_access(validation_request, uow)
            if not validation_result.is_valid:
                return ResponseQueryResponse(
                    success=False,
                    query_type=query.query_type,
                    total_count=0,
                    returned_count=0,
                    forms=None,
                    responses=None,
                    pagination=None
                )
            
            # Parse client identifiers if available
            client_identifiers = None
            if response.client_identifiers:
                try:
                    client_identifiers = ClientIdentifierSet.model_validate(response.client_identifiers)
                except ValidationError:
                    pass
            
            response_summary = ResponseSummary(
                id=response.id,
                response_id=response.response_id,
                form_id=response.form_id,
                client_identifiers=client_identifiers,
                submitted_at=response.submitted_at,
                processed_at=response.processed_at,
                response_data=response.response_data
            )
            
            return ResponseQueryResponse(
                success=True,
                query_type=query.query_type,
                total_count=1,
                returned_count=1,
                forms=None,
                responses=[response_summary],
                pagination=None
            )
            
        elif query.query_type == QueryType.RESPONSES_BY_USER:
            # Get all responses for user's forms
            user_forms = await uow.onboarding_forms.get_by_user_id(query.user_id)
            
            all_responses = []
            for form in user_forms:
                form_responses = await uow.form_responses.get_by_form_id(form.id)
                all_responses.extend(form_responses)
            
            response_summaries = []
            for response in all_responses:
                # Parse client identifiers if available
                client_identifiers = None
                if response.client_identifiers:
                    try:
                        client_identifiers = ClientIdentifierSet.model_validate(response.client_identifiers)
                    except ValidationError:
                        pass
                
                response_summary = ResponseSummary(
                    id=response.id,
                    response_id=response.response_id,
                    form_id=response.form_id,
                    client_identifiers=client_identifiers,
                    submitted_at=response.submitted_at,
                    processed_at=response.processed_at,
                    response_data=None  # Don't include full data for bulk queries
                )
                response_summaries.append(response_summary)
            
            # Sort by submission date (newest first)
            response_summaries.sort(key=lambda r: r.submitted_at, reverse=True)
            
            # Apply pagination
            total_count = len(response_summaries)
            start_idx = query.offset if query.offset is not None else 0
            end_idx = start_idx + (query.limit if query.limit is not None else 50)
            paginated_responses = response_summaries[start_idx:end_idx]
            
            return ResponseQueryResponse(
                success=True,
                query_type=query.query_type,
                total_count=total_count,
                returned_count=len(paginated_responses),
                forms=None,
                responses=paginated_responses,
                pagination={
                    "offset": query.offset,
                    "limit": query.limit,
                    "has_more": end_idx < total_count
                }
            )
        
        else:
            raise ValueError(f"Unsupported query type: {query.query_type}")
            
    except Exception as e:
        logger.error(f"Error executing query {query.query_type}: {str(e)}")
        return ResponseQueryResponse(
            success=False,
            query_type=query.query_type,
            total_count=0,
            returned_count=0,
            forms=None,
            responses=None,
            pagination=None
        ) 