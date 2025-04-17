from dataclasses import dataclass


@dataclass
class ContactInfoSaModel:
    main_phone: str
    main_email: str
    all_phones: list[str]
    all_emails: list[str]
