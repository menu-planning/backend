import datetime

from pydantic import BaseModel

from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.domain.enums import Weekday


class ApiMenuMeal(BaseModel, frozen=True):
    meal_id: str
    meal_name: str
    nutri_facts: ApiNutriFacts | None = None
    week: int
    weekday: Weekday
    hour: datetime.time | None = None
    meal_type: MealType

    @classmethod
    def from_domain(cls, domain_obj: MenuMeal) -> "ApiMenuMeal":
        try:
            return cls(
                meal_id=domain_obj.meal_id,
                meal_name=domain_obj.meal_name,
                nutri_facts=(
                    ApiNutriFacts.from_domain(domain_obj.nutri_facts)
                    if domain_obj.nutri_facts
                    else None
                ),
                week=domain_obj.week,
                weekday=domain_obj.weekday,
                hour=domain_obj.hour,
                meal_type=domain_obj.meal_type,
            )
        except Exception as e:
            raise ValueError(f"Failed to build ApiMenuMeal from domain instance: {e}")

    def to_domain(self) -> MenuMeal:
        try:
            return MenuMeal(
                meal_id=self.meal_id,
                meal_name=self.meal_name,
                nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
                week=self.week,
                weekday=self.weekday,
                hour=self.hour,
                meal_type=self.meal_type,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to MenuMeal: {e}") from e
