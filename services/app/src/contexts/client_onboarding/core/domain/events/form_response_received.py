from attrs import define, field
from typing import Dict, Any
from src.contexts.seedwork.shared.domain.event import Event


@define
class FormResponseReceived(Event):
    """
    Event published when a webhook receives a TypeForm response.
    
    This event contains the raw form response data and triggers
    downstream processing.
    """
    
    form_id: int  # Internal onboarding form ID
    typeform_response_id: str  # TypeForm's response ID
    response_data: Dict[str, Any]  # Raw response data from TypeForm
    webhook_timestamp: str  # When webhook was received
    id: str = field(factory=Event.generate_uuid) 