from attrs import frozen

from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject

@frozen(kw_only=True)
class ContactInfo:
    """Represents client contact details."""
    main_phone: str | None
    main_email: str | None
    all_phones: set[str]
    all_emails: set[str]