import uuid


class Event:
    @staticmethod
    def generate_uuid() -> str:
        return uuid.uuid4().hex
