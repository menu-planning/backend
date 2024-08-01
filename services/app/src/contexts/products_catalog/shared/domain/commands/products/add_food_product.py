from collections.abc import Mapping

from attrs import field, frozen
from src.contexts.products_catalog.shared.domain.value_objects.score import Score
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


@frozen
class AddFoodProduct(Command):
    source_id: str
    name: str
    category_id: str
    parent_category_id: str
    nutri_facts: NutriFacts = field(
        converter=lambda x: NutriFacts(**x) if x and isinstance(x, Mapping) else x
    )
    score: Score = field(
        default=None,
        converter=lambda x: Score(**x) if x and isinstance(x, Mapping) else x,
    )
    diet_types_ids: set[str] | None = None
    food_group_id: str | None = None
    process_type_id: str | None = None
    ingredients: str | None = None
    allergens: set[Allergen] | None = None
    package_size: float | None = None
    package_size_unit: str | None = None
    brand_id: str | None = None
    barcode: str | None = None
    image_url: str | None = None
    json_data: str | None = None
