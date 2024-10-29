from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.tags.base_class import (
    TagSaModel,
)


class MealPlanningSaModel(TagSaModel):
    __mapper_args__ = {
        "polymorphic_identity": "meal_planning",
    }
