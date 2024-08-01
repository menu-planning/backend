from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture


@frozen
class DietaryPreferences(ValueObject):
    preferred_foods: list[str]
    required_dishes: list[str]
    preferred_flavors: list[Flavor]
    disliked_flavors: list[Flavor]
    preferred_textures: list[Texture]
    disliked_textures: list[Texture]
    preferred_cuisines: list[Cuisine]
    disliked_cuisines: list[Cuisine]
    allergies: list[Allergen]
    restrictions: list[DietType]
