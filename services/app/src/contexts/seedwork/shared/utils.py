from datetime import datetime

from cattrs import Converter

converter = Converter()

converter.register_unstructure_hook(datetime, lambda dt: dt.isoformat())
converter.register_structure_hook(datetime, lambda ts, _: datetime.fromisoformat(ts))
