from pydantic import BaseModel


class ApiAddMenuItem(BaseModel):
    menu_id: str
    meal: ApiMe

    def to_domain(self) -> AddMenuItem:
        return AddMenuItem(
            menu_id=self.menu_id,
            meal=self.meal.to_domain(),
        )
