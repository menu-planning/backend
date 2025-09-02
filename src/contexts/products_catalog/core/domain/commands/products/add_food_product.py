"""Command to add a new food product to the catalog."""
from collections.abc import Mapping

from attrs import field, frozen
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


@frozen
class AddFoodProduct(Command):
    """Command to add a new food product to the catalog.
    
    Attributes:
        source_id: Identifier of the data source system.
        name: Product name.
        nutri_facts: Nutritional information for the product.
        score: Product quality or rating score.
        category_id: Product category identifier.
        parent_category_id: Parent category identifier for hierarchical classification.
        food_group_id: Food group classification identifier.
        process_type_id: Food processing type identifier.
        ingredients: List of ingredients in the product.
        package_size: Size of the product package.
        package_size_unit: Unit of measurement for package size.
        brand_id: Brand identifier.
        barcode: Product barcode if available.
        image_url: URL to product image.
        json_data: Additional product data in JSON format.
    
    Notes:
        Creates a new food product with nutritional and classification data.
        Emits FoodProductCreated event upon successful creation.
    """
    source_id: str
    name: str
    nutri_facts: NutriFacts = field(
        converter=lambda x: NutriFacts(**x) if x and isinstance(x, Mapping) else x
    )
    score: Score = field(
        default=None,
        converter=lambda x: Score(**x) if x and isinstance(x, Mapping) else x,
    )
    category_id: str | None = None
    parent_category_id: str | None = None
    food_group_id: str | None = None
    process_type_id: str | None = None
    ingredients: str | None = None
    package_size: float | None = None
    package_size_unit: str | None = None
    brand_id: str | None = None
    barcode: str | None = None
    image_url: str | None = None
    json_data: str | None = None
