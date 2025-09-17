from attr import asdict
from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.recipes_catalog.core.domain.client.events.menu_meals_changed import (
    MenuMealAddedOrRemoved,
)
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import (
    MenuMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.commands.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal


def add_newly_created_meal_to_menu(
    menu: Menu, create_meal_cmd: CreateMeal
) -> tuple[Menu, Meal]:
    """Add a newly created meal to the menu."""
    assert create_meal_cmd.menu_meal is not None, "Menu meal is required"
    kwargs = asdict(create_meal_cmd, recurse=False)
    kwargs.pop("menu_meal")
    meal = Meal.create_meal(**kwargs)
    new_menu_meal = create_meal_cmd.menu_meal.replace(
        meal_id=meal.id,
        meal_name=meal.name,
        nutri_facts=meal.nutri_facts,
    )
    menu.add_meal(new_menu_meal)
    # remove the event that was added by the add_meal method
    for i in range(len(menu.events)):
        if isinstance(menu.events[i], MenuMealAddedOrRemoved):
            menu.events.pop(i)
            break
    return menu, meal
