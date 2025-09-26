"""Command handler for creating clients, with optional form response mapping."""
from typing import Any, Callable, Optional

from attrs import asdict
from src.contexts.recipes_catalog.core.adapters.other_ctx_providers.client_onboarding.client_onboarding_provider import (
    ClientOnboardingProvider,
)
from src.contexts.recipes_catalog.core.domain.client.commands.create_client import (
    CreateClient,
)
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.recipes_catalog.core.services.client.form_response_mapper import (
    FormResponseMapper,
)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork


async def create_client_handler(cmd: CreateClient, uow_factory: Callable[[],UnitOfWork]) -> None:
    """Create a client from command data; optionally merge Typeform response."""
    async with uow_factory() as uow:
        # Check if this includes form response integration
        form_response_id = getattr(cmd, 'form_response_id', None)
        if form_response_id:
            client_params = await _prepare_client_params_with_form_response(cmd, form_response_id)
        else:
            # Standard client creation - convert command to dict and add onboarding_data as None
            client_params = asdict(cmd, recurse=False)
            client_params['onboarding_data'] = None  # No form response data

        client = Client.create_client(**client_params)
        await uow.clients.add(client)
        await uow.commit()


async def _prepare_client_params_with_form_response(cmd: CreateClient, form_response_id: str) -> dict[str, Any]:
    """Combine command attributes with fetched form response data (command wins)."""
    # Fetch form response data from client_onboarding context
    form_response_data = await ClientOnboardingProvider.get_form_response(form_response_id)

    # Initialize form response mapper
    mapper = FormResponseMapper()

    # Map form response to client data
    form_client_params, extraction_warnings = mapper.map_form_response_to_client_data(
        form_response=form_response_data,
        author_id=cmd.author_id
    )

    # Start with command attributes (these take precedence)
    cmd_dict = asdict(cmd, recurse=False)

    # Remove form_response_id from final params since it's not a Client attribute
    cmd_dict.pop('form_response_id', None)

    # Prepare final client creation parameters
    client_params = {}

    # Required fields - always use command values
    client_params['author_id'] = cmd.author_id

    # Profile - use command if provided, otherwise use form data
    if cmd.profile is not None:
        client_params['profile'] = cmd.profile
    elif form_client_params.get('profile'):
        client_params['profile'] = form_client_params['profile']
    else:
        # This should not happen as profile is required, but fallback to command
        client_params['profile'] = cmd.profile

    # Optional fields - command takes precedence, fall back to form data

    # Contact Info
    if cmd.contact_info is not None:
        client_params['contact_info'] = cmd.contact_info
    elif form_client_params.get('contact_info'):
        client_params['contact_info'] = form_client_params['contact_info']
    else:
        client_params['contact_info'] = None

    # Address
    if cmd.address is not None:
        client_params['address'] = cmd.address
    elif form_client_params.get('address'):
        client_params['address'] = form_client_params['address']
    else:
        client_params['address'] = None

    # Tags
    if cmd.tags is not None:
        client_params['tags'] = cmd.tags
    elif form_client_params.get('tags'):
        client_params['tags'] = form_client_params['tags']
    else:
        client_params['tags'] = None

    # Notes - combine command notes with form extraction notes
    if cmd.notes is not None:
        if form_client_params.get('notes'):
            # Combine command notes with form notes
            client_params['notes'] = f"{cmd.notes}\n\n--- Form Response Data ---\n{form_client_params['notes']}"
        else:
            client_params['notes'] = cmd.notes
    elif form_client_params.get('notes'):
        client_params['notes'] = form_client_params['notes']
    else:
        client_params['notes'] = None

    # Onboarding Data - always store the fetched form response data
    client_params['onboarding_data'] = form_response_data

    return client_params
