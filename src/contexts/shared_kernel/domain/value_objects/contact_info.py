from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True)
class ContactInfo(ValueObject):
    """Value object representing client contact details.

    Attributes:
        main_phone: Primary phone number.
        main_email: Primary email address.
        all_phones: Set of all phone numbers.
        all_emails: Set of all email addresses.

    Notes:
        Immutable. Equality by value (all fields).
    """

    main_phone: str | None
    main_email: str | None
    all_phones: frozenset[str]
    all_emails: frozenset[str]
