from pydantic import BaseModel

from src.contexts.recipes_catalog.core.domain.commands.recipe.delete import (
    DeleteRecipe,
)


class ApiDeleteRecipe(BaseModel):
    recipe_id: str

    def to_domain(self) -> DeleteRecipe:
        """Converts the instance to a domain model object for adding a recipe."""
        try:
            return DeleteRecipe(
                recipe_id=self.recipe_id,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCopyRecipe to domain model: {e}")
