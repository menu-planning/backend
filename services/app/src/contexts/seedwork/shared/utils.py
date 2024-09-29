from datetime import datetime

from cattrs import Converter

converter = Converter()

converter.register_unstructure_hook(datetime, lambda dt: dt.isoformat())
converter.register_structure_hook(datetime, lambda ts, _: datetime.fromisoformat(ts))


def custom_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    raise TypeError("Type not serializable")
