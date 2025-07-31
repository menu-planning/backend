from attrs import define, field
from typing import Dict, Any
from src.contexts.seedwork.shared.domain.event import Event


@define
class ClientDataExtracted(Event):
    """
    Event published when client data has been extracted and processed from a form response.
    
    This event signals that structured client data is ready for integration
    with the recipes_catalog context.
    """
    
    form_response_id: int  # Internal form response ID
    extracted_client_data: Dict[str, Any]  # Processed client information
    client_identifiers: Dict[str, str]  # Name, email, etc. for client creation
    user_id: int  # User who owns the form
    id: str = field(factory=Event.generate_uuid) 