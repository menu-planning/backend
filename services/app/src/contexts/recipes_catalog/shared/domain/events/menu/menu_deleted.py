from attrs import frozen


@frozen
class MenuDeleted:
    menu_id: str
    keep_meals: bool
