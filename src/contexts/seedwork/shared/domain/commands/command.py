import uuid


class Command:
    @staticmethod
    def generate_uuid() -> str:
        return uuid.uuid4().hex
