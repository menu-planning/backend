from pydantic import BaseModel, Field


class ProductsCatalogProduct(BaseModel):
    """API schema for products catalog product representation.

    Represents a product from the products catalog context with all
    available metadata including nutritional information, categorization,
    and dietary classifications.

    Attributes:
        id: Unique product identifier.
        source_id: Source system identifier.
        name: Product name.
        is_food: Whether the product is classified as food.
        barcode: Product barcode if available.
        brand_id: Brand identifier if applicable.
        category_id: Primary category identifier.
        parent_category_id: Parent category identifier for hierarchical categorization.
        score: Product scoring/rating data.
        food_group_id: Food group classification identifier.
        process_type_id: Processing type identifier.
        diet_types_ids: Set of dietary restriction/classification identifiers.
        nutri_facts: Nutritional facts and composition data.
        ingredients: Ingredient list as text.
        package_size: Package size quantity.
        package_size_unit: Unit of measurement for package size.
        image_url: Product image URL if available.
        is_food_houses_choice: Whether product is marked as house choice.
    """

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
