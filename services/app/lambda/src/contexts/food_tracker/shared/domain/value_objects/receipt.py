from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class Receipt(ValueObject):
    cfe_key: str
    qrcode: str | None = None
