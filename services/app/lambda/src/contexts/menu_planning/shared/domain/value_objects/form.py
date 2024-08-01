from datetime import datetime
from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen
class FormResponse(ValueObject):
    form_id: str
    form_name: str
    client_id: str
    submitted_at: datetime
    landed_at: datetime
    complete_json_response: dict[str, Any]
