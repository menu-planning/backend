from typing import Dict, Any, Optional
from src.contexts.recipes_catalog.core.domain.client.commands.update_client import UpdateClient
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.recipes_catalog.core.services.client.form_response_mapper import FormResponseMapper
from src.contexts.recipes_catalog.core.adapters.external_providers.client_onboarding.client_onboarding_provider import ClientOnboardingProvider


async def update_client_handler(cmd: UpdateClient, uow: UnitOfWork) -> None:
    """
    Enhanced update client handler with form response data processing support.
    
    Supports two modes:
    1. Standard update: Direct property updates via cmd.updates
    2. Form response integration: Automatic mapping from TypeForm response data
    
    Form Response Integration Mode:
    - If 'form_response_id' is provided in cmd.updates, fetches the form response
    - Maps form data to Client properties (profile, contact_info, address)  
    - Stores original form data in onboarding_data field
    - Updates existing Client with mapped data while preserving existing properties
    """
    async with uow:
        client = await uow.clients.get(cmd.client_id)
        
        # Check if this is a form response integration update
        form_response_id = cmd.updates.get('form_response_id')
        if form_response_id:
            await _handle_form_response_update(client, form_response_id, cmd.updates)
        else:
            # Standard property update
            client.update_properties(**cmd.updates)
        
        await uow.clients.persist(client)
        await uow.commit()


async def _handle_form_response_update(client, form_response_id: str, updates: Dict[str, Any]) -> None:
    """
    Handle form response integration for client updates.
    
    Args:
        client: The Client entity to update
        form_response_id: TypeForm response ID to fetch and process
        updates: Additional updates to apply alongside form data
    """
    # Fetch form response data from client_onboarding context
    form_response_data = await ClientOnboardingProvider.get_form_response(form_response_id)
    
    # Initialize form response mapper
    mapper = FormResponseMapper()
    
    # Map form response to client data (excluding author_id since this is an update)
    client_params, extraction_warnings = mapper.map_form_response_to_client_data(
        form_response=form_response_data, 
        author_id=client.author_id
    )
    
    # Prepare update parameters, excluding read-only fields
    update_params = {}
    
    # Update profile if extracted and not explicitly overridden in updates
    if client_params.get('profile') and 'profile' not in updates:
        update_params['profile'] = client_params['profile']
    
    # Update contact_info if extracted and not explicitly overridden
    if client_params.get('contact_info') and 'contact_info' not in updates:
        update_params['contact_info'] = client_params['contact_info']
    
    # Update address if extracted and not explicitly overridden
    if client_params.get('address') and 'address' not in updates:
        update_params['address'] = client_params['address']
    
    # Always update onboarding_data with the form response unless explicitly overridden
    if 'onboarding_data' not in updates:
        update_params['onboarding_data'] = form_response_data
    
    # Update notes with extraction information unless explicitly overridden
    if client_params.get('notes') and 'notes' not in updates:
        existing_notes = client.notes or ""
        form_notes = client_params['notes']
        if existing_notes and form_notes:
            update_params['notes'] = f"{existing_notes}\n\n--- Form Response Data ---\n{form_notes}"
        elif form_notes:
            update_params['notes'] = form_notes
    
    # Apply any explicit updates from the command (these take priority)
    update_params.update({k: v for k, v in updates.items() if k != 'form_response_id'})
    
    # Apply all updates to the client
    client.update_properties(**update_params)
