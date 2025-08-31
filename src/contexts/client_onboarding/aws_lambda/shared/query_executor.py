"""
Shared query execution logic for response query Lambda handlers.

Contains the core business logic for executing different types of response queries
that can be reused across multiple Lambda functions.
"""

from contextlib import suppress

from pydantic import ValidationError
from src.contexts.client_onboarding.core.adapters import FormOwnershipValidator
from src.contexts.client_onboarding.core.adapters.api_schemas.queries import (
    FormSummary,
    QueryType,
    ResponseQueryRequest,
    ResponseQueryResponse,
    ResponseSummary,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses import (
    ClientIdentifierSet,
)
from src.contexts.client_onboarding.core.adapters.validators import (
    OwnershipValidationRequest,
)
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)

# Constants
SMALL_QUERY_LIMIT = 10
DEFAULT_PAGINATION_LIMIT = 50


def _create_pagination_info(
    offset: int | None, limit: int | None, total_count: int
) -> dict:
    """Create pagination information dictionary."""
    return {
        "offset": offset,
        "limit": limit,
        "has_more": (offset or 0) + (limit or DEFAULT_PAGINATION_LIMIT) < total_count,
    }


def _parse_client_identifiers(client_identifiers_data) -> ClientIdentifierSet | None:
    """Parse client identifiers with error handling."""
    if not client_identifiers_data:
        return None

    with suppress(ValidationError):
        return ClientIdentifierSet.model_validate(client_identifiers_data)
    return None


def _create_form_summary(form, responses: list) -> FormSummary:
    """Create a form summary from form and responses data."""
    return FormSummary(
        id=form.id,
        typeform_id=form.typeform_id,
        title=form.typeform_id,  # Use typeform_id as title since no title field exists
        status=form.status.value,
        created_at=form.created_at,
        updated_at=form.updated_at,
        response_count=len(responses),
    )


def _create_response_summary(
    response, *, include_full_data: bool = False
) -> ResponseSummary:
    """Create a response summary from response data."""
    client_identifiers = _parse_client_identifiers(response.client_identifiers)

    return ResponseSummary(
        id=response.id,
        response_id=response.response_id,
        form_id=response.form_id,
        client_identifiers=client_identifiers,
        submitted_at=response.submitted_at,
        processed_at=response.processed_at,
        response_data=response.response_data if include_full_data else None,
    )


def _apply_pagination(items: list, offset: int | None, limit: int | None) -> list:
    """Apply pagination to a list of items."""
    start_idx = offset if offset is not None else 0
    end_idx = start_idx + (limit if limit is not None else DEFAULT_PAGINATION_LIMIT)
    return items[start_idx:end_idx]


async def _execute_forms_by_user_query(
    query: ResponseQueryRequest, uow: UnitOfWork
) -> ResponseQueryResponse:
    """Execute FORMS_BY_USER query type."""
    forms = await uow.onboarding_forms.get_by_user_id(query.user_id)

    form_summaries = []
    for form in forms:
        responses = await uow.form_responses.get_by_form_id(form.id)
        form_summary = _create_form_summary(form, responses)
        form_summaries.append(form_summary)

    total_count = len(form_summaries)
    paginated_forms = _apply_pagination(form_summaries, query.offset, query.limit)

    return ResponseQueryResponse(
        success=True,
        query_type=query.query_type,
        total_count=total_count,
        returned_count=len(paginated_forms),
        forms=paginated_forms,
        responses=None,
        pagination=_create_pagination_info(query.offset, query.limit, total_count),
    )


async def _execute_responses_by_form_query(
    query: ResponseQueryRequest,
    uow: UnitOfWork,
    ownership_validator: FormOwnershipValidator,
) -> ResponseQueryResponse:
    """Execute RESPONSES_BY_FORM query type."""
    if query.form_id is None:
        return ResponseQueryResponse(
            success=False,
            query_type=query.query_type,
            total_count=0,
            returned_count=0,
            forms=None,
            responses=None,
            pagination=None,
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
            pagination=None,
        )

    validation_request = OwnershipValidationRequest(
        user_id=query.user_id,
        form_id=form.typeform_id,
        onboarding_form_id=None,
        operation="query_responses",
    )
    validation_result = await ownership_validator.validate_form_access(
        validation_request, uow
    )
    if not validation_result.is_valid:
        return ResponseQueryResponse(
            success=False,
            query_type=query.query_type,
            total_count=0,
            returned_count=0,
            forms=None,
            responses=None,
            pagination=None,
        )

    # Get responses for the form
    responses = await uow.form_responses.get_by_form_id(query.form_id)

    response_summaries = []
    include_full_data = query.limit is not None and query.limit <= SMALL_QUERY_LIMIT

    for response in responses:
        response_summary = _create_response_summary(
            response, include_full_data=include_full_data
        )
        response_summaries.append(response_summary)

    total_count = len(response_summaries)
    paginated_responses = _apply_pagination(
        response_summaries, query.offset, query.limit
    )

    return ResponseQueryResponse(
        success=True,
        query_type=query.query_type,
        total_count=total_count,
        returned_count=len(paginated_responses),
        forms=None,
        responses=paginated_responses,
        pagination=_create_pagination_info(query.offset, query.limit, total_count),
    )


async def _execute_response_by_id_query(
    query: ResponseQueryRequest,
    uow: UnitOfWork,
    ownership_validator: FormOwnershipValidator,
) -> ResponseQueryResponse:
    """Execute RESPONSE_BY_ID query type."""
    if query.response_id is None:
        return ResponseQueryResponse(
            success=False,
            query_type=query.query_type,
            total_count=0,
            returned_count=0,
            forms=None,
            responses=None,
            pagination=None,
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
            pagination=None,
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
            pagination=None,
        )

    validation_request = OwnershipValidationRequest(
        user_id=query.user_id,
        form_id=form.typeform_id,
        onboarding_form_id=None,
        operation="query_response_by_id",
    )
    validation_result = await ownership_validator.validate_form_access(
        validation_request, uow
    )
    if not validation_result.is_valid:
        return ResponseQueryResponse(
            success=False,
            query_type=query.query_type,
            total_count=0,
            returned_count=0,
            forms=None,
            responses=None,
            pagination=None,
        )

    response_summary = _create_response_summary(response, include_full_data=True)

    return ResponseQueryResponse(
        success=True,
        query_type=query.query_type,
        total_count=1,
        returned_count=1,
        forms=None,
        responses=[response_summary],
        pagination=None,
    )


async def _execute_responses_by_user_query(
    query: ResponseQueryRequest, uow: UnitOfWork
) -> ResponseQueryResponse:
    """Execute RESPONSES_BY_USER query type."""
    user_forms = await uow.onboarding_forms.get_by_user_id(query.user_id)

    all_responses = []
    for form in user_forms:
        form_responses = await uow.form_responses.get_by_form_id(form.id)
        all_responses.extend(form_responses)

    response_summaries = []
    for response in all_responses:
        response_summary = _create_response_summary(response, include_full_data=False)
        response_summaries.append(response_summary)

    # Sort by submission date (newest first)
    response_summaries.sort(key=lambda r: r.submitted_at, reverse=True)

    total_count = len(response_summaries)
    paginated_responses = _apply_pagination(
        response_summaries, query.offset, query.limit
    )

    return ResponseQueryResponse(
        success=True,
        query_type=query.query_type,
        total_count=total_count,
        returned_count=len(paginated_responses),
        forms=None,
        responses=paginated_responses,
        pagination=_create_pagination_info(query.offset, query.limit, total_count),
    )


def _handle_unsupported_query_type(query_type: QueryType) -> None:
    """Handle unsupported query types by raising an appropriate error."""
    error_message = f"Unsupported query type: {query_type}"
    raise ValueError(error_message)


async def execute_query(
    query: ResponseQueryRequest,
    uow: UnitOfWork,
    ownership_validator: FormOwnershipValidator,
) -> ResponseQueryResponse:
    """Execute a single query operation."""
    try:
        if query.query_type == QueryType.FORMS_BY_USER:
            return await _execute_forms_by_user_query(query, uow)

        if query.query_type == QueryType.RESPONSES_BY_FORM:
            return await _execute_responses_by_form_query(
                query, uow, ownership_validator
            )

        if query.query_type == QueryType.RESPONSE_BY_ID:
            return await _execute_response_by_id_query(query, uow, ownership_validator)

        if query.query_type == QueryType.RESPONSES_BY_USER:
            return await _execute_responses_by_user_query(query, uow)

        _handle_unsupported_query_type(query.query_type)
        # This line is unreachable due to the exception raised above
        return ResponseQueryResponse(
            success=False,
            query_type=query.query_type,
            total_count=0,
            returned_count=0,
            forms=None,
            responses=None,
            pagination=None,
        )

    except Exception as e:
        logger.error("Error executing query", query_type=query.query_type, error=str(e), action="query_execution_error")
        return ResponseQueryResponse(
            success=False,
            query_type=query.query_type,
            total_count=0,
            returned_count=0,
            forms=None,
            responses=None,
            pagination=None,
        )
