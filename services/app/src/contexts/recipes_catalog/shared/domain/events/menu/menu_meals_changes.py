from attrs import frozen


@frozen(hash=True)
class MenuMealsChanged:
    menu_id: str
    new_meals_ids: list[str]
    removed_meals_ids: list[str]
