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
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.logging.logger import get_logger

logger = get_logger(__name__)

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
    return (menu, meal)

async def update_menu_meals_and_manage_related_meals(menu: Menu, new_meals_value: set[MenuMeal], uow: UnitOfWork) -> Menu:
    ids_of_current_meals_on_menu = {meal.meal_id for meal in menu.meals}
    ids_of_meals_on_new_menu_meals = [meal.meal_id for meal in new_meals_value]

    unique_ids_of_meals_on_new_menu_meals = set(ids_of_meals_on_new_menu_meals)
    ids_of_meals_to_removed_from_menu = ids_of_current_meals_on_menu - unique_ids_of_meals_on_new_menu_meals
    all_meals_in_transaction = await uow.meals.query(
            filters={"id": list(unique_ids_of_meals_on_new_menu_meals.union(ids_of_current_meals_on_menu))}
        )
    

    new_set_of_menu_meals_for_menu = set()
    for meal in all_meals_in_transaction:
        if meal.id in ids_of_meals_to_removed_from_menu:
            logger.error(f"meal.id: {meal.id} in ids_of_meals_to_removed_from_menu")
            meal._menu_id = None
            await uow.meals.persist(meal)
        else:
            ids_of_meals_already_in_menu = []
            for menu_meal in [i for i in new_meals_value if i.meal_id == meal.id]:
                if menu_meal.meal_id not in ids_of_meals_already_in_menu:
                    meal._menu_id = menu.id # just make sure menu_id is correct
                    await uow.meals.persist(meal)
                    new_set_of_menu_meals_for_menu.add(menu_meal)
                    ids_of_meals_already_in_menu.append(menu_meal.meal_id)
                else:
                    new_meal = Meal.copy_meal(
                        meal=meal,
                        id_of_user_coping_meal=menu.author_id,
                        id_of_target_menu=menu.id,
                    )
                    await uow.meals.add(new_meal)
                    new_set_of_menu_meals_for_menu.add(menu_meal.replace(meal_id=new_meal.id))

    menu.meals = new_set_of_menu_meals_for_menu
    return menu