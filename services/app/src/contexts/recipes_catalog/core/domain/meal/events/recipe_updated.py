from src.contexts.seedwork.shared.domain.event import Event


class RecipeUpdated(Event):
    recipe_id: str
