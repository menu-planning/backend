from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.enums import Privacy


@frozen(kw_only=True)
class CreateDietType(Command):
    name: str
    author_id: str
    privacy: Privacy = Privacy.PRIVATE
    description: str | None = None
