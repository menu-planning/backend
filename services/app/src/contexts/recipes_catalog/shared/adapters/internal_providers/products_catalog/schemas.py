from pydantic import BaseModel, Field


class ProductsCatalogProduct(BaseModel):
    id: str
    source_id: str
    name: str
    is_food: bool
    barcode: str | None = None
    brand_id: str | None = None
    category_id: str | None = None
    parent_category_id: str | None = None
    score: dict | None = None
    food_group_id: str | None = None
    process_type_id: str | None = None
    diet_types_ids: set[str] = Field(default_factory=set)
    nutri_facts: dict | None = None
    ingredients: str | None = None
    package_size: float | None = None
    package_size_unit: str | None = None
    image_url: str | None = None
    is_food_houses_choice: bool | None = None
