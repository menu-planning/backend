from dataclasses import dataclass


@dataclass
class ContactInfoSaModel:
    """SQLAlchemy composite dataclass for contact information fields.

    Attributes:
        main_phone: Primary phone number.
        main_email: Primary email address.
        all_phones: List of all phone numbers.
        all_emails: List of all email addresses.

    Notes:
        Dataclass mirror used for ORM composite contact info fields.
        All fields are optional to support partial contact data.
    """
    main_phone: str | None = None
    main_email: str | None = None
    all_phones: list[str] | None = None
    all_emails: list[str] | None = None
