from dataclasses import dataclass


@dataclass
class ContactInfoSaModel:
    main_phone: str | None = None
    main_email: str | None = None
    all_phones: list[str] | None = None
    all_emails: list[str] | None = None
