from dataclasses import asdict
from typing import Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.value_objects.api_menu_meal_fields import (
    MealTimeOptional,
    MealTypeRequired,
    WeekdayRequired,
    WeekNumberRequired,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_meal_sa_model import (
    MenuMealSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields import (
    MealNameRequired,
    MealNutriFactsOptional,
)
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import (
    MenuMeal,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.domain.enums import Weekday


class ApiMenuMeal(BaseApiValueObject[MenuMeal, MenuMealSaModel]):
    """
    A Pydantic model representing and validating a meal in a menu.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): The unique identifier of the meal.
        meal_name (str): The name of the meal.
        nutri_facts (ApiNutriFacts, optional): The nutritional facts of the meal.
        week (int): The week number in the menu.
        weekday (str): The day of the week.
        hour (time, optional): The time of the meal.
        meal_type (str): The type of meal (e.g., breakfast, lunch, dinner).
    """

    meal_id: UUIDIdRequired
    meal_name: MealNameRequired
    nutri_facts: MealNutriFactsOptional
    week: WeekNumberRequired
    weekday: WeekdayRequired
    hour: MealTimeOptional
    meal_type: MealTypeRequired

    @classmethod
    def from_domain(cls, domain_obj: MenuMeal) -> "ApiMenuMeal":
        """Creates an instance of `ApiMenuMeal` from a domain model object."""
        return cls(
            meal_id=domain_obj.meal_id,
            meal_name=domain_obj.meal_name,
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            week=domain_obj.week,
            weekday=Weekday(domain_obj.weekday),
            hour=domain_obj.hour,
            meal_type=domain_obj.meal_type,
        )

    def to_domain(self) -> MenuMeal:
        """Converts the instance to a domain model object."""
        return MenuMeal(
            meal_id=self.meal_id,
            meal_name=self.meal_name,
            nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
            week=self.week,
            weekday=self.weekday.value,
            hour=self.hour,
            meal_type=self.meal_type,
        )

    @classmethod
    def from_orm_model(cls, orm_model: MenuMealSaModel) -> "ApiMenuMeal":
        """Create an instance from an ORM model."""
        # nutri_facts = None
        # if orm_model.nutri_facts:
        #     if isinstance(orm_model.nutri_facts, dict):
        #         nutri_facts = ApiNutriFacts(**orm_model.nutri_facts)
        #     elif is_dataclass(orm_model.nutri_facts):
        #         # Convert NutriFactsSaModel to dict
        #         nutri_facts_dict = asdict(orm_model.nutri_facts)
        #         nutri_facts = ApiNutriFacts(**nutri_facts_dict)
        return cls(
            meal_id=orm_model.meal_id,
            meal_name=orm_model.meal_name,
            nutri_facts=ApiNutriFacts(**asdict(orm_model.nutri_facts)) if orm_model.nutri_facts else None,
            week=int(orm_model.week),  # Convert string to int
            weekday=Weekday(orm_model.weekday),
            hour=orm_model.hour,
            meal_type=orm_model.meal_type,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert to ORM model kwargs."""
        return {
            "meal_id": self.meal_id,
            "meal_name": self.meal_name,
            "nutri_facts": NutriFactsSaModel(**self.nutri_facts.model_dump()) if self.nutri_facts else None,
            "week": str(self.week),
            "weekday": self.weekday.value,
            "hour": self.hour,
            "meal_type": self.meal_type,
        }
