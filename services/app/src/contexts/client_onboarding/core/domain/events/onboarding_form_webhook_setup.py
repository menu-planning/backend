from attrs import define, field
from src.contexts.seedwork.shared.domain.event import Event


@define
class OnboardingFormWebhookSetup(Event):
    """
    Event published when an onboarding form webhook is successfully set up.
    
    This event signals that a TypeForm webhook has been configured and is ready
    to receive form responses.
    """
    
    user_id: int
    typeform_id: str
    webhook_url: str
    form_id: int  # Internal onboarding form ID
    id: str = field(factory=Event.generate_uuid) 