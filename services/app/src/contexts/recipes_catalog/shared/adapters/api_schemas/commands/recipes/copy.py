from pydantic import BaseModel
from src.contexts.recipes_catalog.shared.domain.commands.recipes.copy import CopyRecipe


class ApiCopyRecipe(BaseModel):
    user_id: str
    recipe_id: str

    def to_domain(self) -> CopyRecipe:
        """Converts the instance to a domain model object for adding a recipe."""
        try:
            return CopyRecipe(
                user_id=self.user_id,
                recipe_id=self.recipe_id,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCopyRecipe to domain model: {e}")
