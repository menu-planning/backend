from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.tags.base_class import (
    TagSaModel,
)


class CategorySaModel(TagSaModel):
    __mapper_args__ = {
        "polymorphic_identity": "category",
    }
