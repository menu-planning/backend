import uuid
from datetime import datetime

from src.contexts.products_catalog.core.domain.events.food_product_created import (
    FoodProductCreated,
)
from src.contexts.products_catalog.core.domain.events.updated_attr_that_reflect_on_recipes import UpdatedAttrOnProductThatReflectOnRecipeShoppingList
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class Product(Entity):
    def __init__(
        self,
        *,
        id: str,
        source_id: str,
        name: str,
        is_food: bool | None = None,
        shopping_name: str | None = None,
        store_department_name: str | None = None,
        recommended_brands_and_products: str | None = None,
        edible_yield: float | None = None,
        kg_per_unit: float | None = None,
        liters_per_kg: float | None = None,
        nutrition_group: str | None = None,
        cooking_factor: float | None = None,
        conservation_days: int | None = None,
        substitutes: str | None = None,
        barcode: str | None = None,
        brand_id: str | None = None,
        category_id: str | None = None,
        parent_category_id: str | None = None,
        score: Score | None = None,
        food_group_id: str | None = None,
        process_type_id: str | None = None,
        nutri_facts: NutriFacts | None = None,
        ingredients: str | None = None,
        package_size: float | None = None,
        package_size_unit: str | None = None,
        image_url: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        json_data: str | None = None,
        discarded: bool = False,
        version: int = 1,
        is_food_votes: IsFoodVotes | None = None,
    ) -> None:
        """Do not call directly to create a new Product."""
        super().__init__(id=id, discarded=discarded, version=version, created_at=created_at, updated_at=updated_at)
        self._source_id = source_id
        self._name = name
        self._is_food = is_food
        self._shopping_name = shopping_name
        self._store_department_name = store_department_name
        self._recommended_brands_and_products = recommended_brands_and_products
        self._edible_yield = edible_yield
        self._kg_per_unit = kg_per_unit
        self._liters_per_kg = liters_per_kg
        self._nutrition_group = nutrition_group
        self._cooking_factor = cooking_factor
        self._conservation_days = conservation_days
        self._substitutes = substitutes
        self._brand_id = brand_id
        self._category_id = category_id
        self._parent_category_id = parent_category_id
        self._score = score
        self._barcode = barcode
        self._food_group_id = food_group_id
        self._process_type_id = process_type_id
        self._nutri_facts = nutri_facts
        self._ingredients = ingredients
        self._package_size = package_size
        self._package_size_unit = package_size_unit
        self._json_data = json_data
        self._image_url = image_url
        self._is_food_votes = is_food_votes or IsFoodVotes() # type: ignore
        self.events: list[Event] = []

    @classmethod
    def add_food_product(
        cls,
        *,
        source_id: str,
        name: str,
        shopping_name: str | None = None,
        store_department_name: str | None = None,
        recommended_brands_and_products: str | None = None,
        edible_yield: float | None = None,
        kg_per_unit: float | None = None,
        liters_per_kg: float | None = None,
        nutrition_group: str | None = None,
        cooking_factor: float | None = None,
        conservation_days: int | None = None,
        substitutes: str | None = None,
        category_id: str | None = None,
        parent_category_id: str | None = None,
        nutri_facts: NutriFacts | None = None,
        # id: str | None = None,
        barcode: str | None = None,
        brand_id: str | None = None,
        score: Score | None = None,
        food_group_id: str | None = None,
        process_type_id: str | None = None,
        ingredients: str | None = None,
        package_size: float | None = None,
        package_size_unit: str | None = None,
        image_url: str | None = None,
        json_data: str | None = None,
        is_food_votes: IsFoodVotes | None = None,
    ) -> "Product":
        # if id is None:
        event = FoodProductCreated(data_source=source_id, barcode=barcode)
        # else:
        # event = FoodProductCreated(product_id=id)
        product = cls(
            id=event.product_id,
            source_id=source_id,
            name=name,
            is_food=True,
            shopping_name=shopping_name,
            store_department_name=store_department_name,
            recommended_brands_and_products=recommended_brands_and_products,
            edible_yield=edible_yield,
            kg_per_unit=kg_per_unit,
            liters_per_kg=liters_per_kg,
            nutrition_group=nutrition_group,
            cooking_factor=cooking_factor,
            conservation_days=conservation_days,
            substitutes=substitutes,
            brand_id=brand_id,
            category_id=category_id,
            parent_category_id=parent_category_id,
            score=score,
            barcode=barcode,
            food_group_id=food_group_id,
            process_type_id=process_type_id,
            nutri_facts=nutri_facts or NutriFacts(),
            ingredients=ingredients,
            package_size=package_size,
            package_size_unit=package_size_unit,
            json_data=json_data,
            image_url=image_url,
            is_food_votes=is_food_votes or IsFoodVotes(), # type: ignore
        )
        product.events.append(event)
        return product

    @classmethod
    def add_non_food_product(
        cls,
        *,
        source_id: str,
        name: str,
        barcode: str,
        image_url: str | None = None,
        is_food_votes=IsFoodVotes(), # type: ignore
    ) -> "Product":
        _id = uuid.uuid4().hex
        product = cls(
            id=_id,
            source_id=source_id,
            name=name,
            barcode=barcode,
            is_food=False,
            image_url=image_url,
            is_food_votes=is_food_votes or IsFoodVotes(), # type: ignore
        )
        return product

    def add_event_to_updated_recipes(self, message: str = "") -> None:
        """Add or update an event indicating this product affects recipes.
        
        This method ensures only one UpdatedAttrOnProductThatReflectOnRecipeShoppingList
        event exists per product, concatenating messages to avoid event proliferation
        while preserving the audit trail of changes.
        
        Args:
            message: Description of the change that affects recipes
        """
        # Find any existing UpdatedAttrOnProductThatReflectOnRecipeShoppingList event
        existing_event = None
        for event in self.events:
            if isinstance(event, UpdatedAttrOnProductThatReflectOnRecipeShoppingList):
                existing_event = event
                break

        # Build new message, avoiding duplication
        new_message = message.strip() if message else ""
        
        if existing_event and existing_event.message:
            existing_messages = [msg.strip() for msg in existing_event.message.split(';') if msg.strip()]
            # Only add new message if it's not already present
            if new_message and new_message not in existing_messages:
                existing_messages.append(new_message)
                new_message = '; '.join(existing_messages)
            else:
                new_message = existing_event.message
        
        # Create new event
        event = UpdatedAttrOnProductThatReflectOnRecipeShoppingList(
            product_id=self.id,
            message=new_message
        )

        # Replace existing event or add new one
        if existing_event:
            self.events[self.events.index(existing_event)] = event
        else:
            self.events.append(event)

    @property
    def source_id(self) -> str:
        self._check_not_discarded()
        return self._source_id

    def _set_source_id(self, value: str) -> None:
        """Protected setter for source_id. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._source_id != value:
            self._source_id = value
            self._increment_version()

    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    def _set_name(self, value: str) -> None:
        """Protected setter for name. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def shopping_name(self) -> str | None:
        self._check_not_discarded()
        return self._shopping_name
    
    def _set_shopping_name(self, value: str | None) -> None:
        """Protected setter for shopping_name. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._shopping_name != value:
            self._shopping_name = value
            self.add_event_to_updated_recipes("Updated shopping name")
            self._increment_version()

    @property
    def store_department_name(self) -> str | None:
        self._check_not_discarded()
        return self._store_department_name
    
    def _set_store_department_name(self, value: str | None) -> None:
        """Protected setter for store_department_name. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._store_department_name != value:
            self._store_department_name = value
            self.add_event_to_updated_recipes("Updated store department")
            self._increment_version()

    @property
    def recommended_brands_and_products(self) -> str | None:
        self._check_not_discarded()
        return self._recommended_brands_and_products
    
    def _set_recommended_brands_and_products(self, value: str) -> None:
        """Protected setter for recommended_brands_and_products. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._recommended_brands_and_products != value:
            self._recommended_brands_and_products = value
            self.add_event_to_updated_recipes("Updated recommended brands")
            self._increment_version()

    @property
    def edible_yield(self) -> float | None:
        self._check_not_discarded()
        return self._edible_yield
    
    def _set_edible_yield(self, value: float) -> None:
        """Protected setter for edible_yield. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._edible_yield != value:
            self._edible_yield = value
            self.add_event_to_updated_recipes("Updated edible yield")
            self._increment_version()

    @property
    def kg_per_unit(self) -> float | None:
        self._check_not_discarded()
        return self._kg_per_unit
    
    def _set_kg_per_unit(self, value: float | None) -> None:
        """Protected setter for kg_per_unit. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._kg_per_unit != value:
            self._kg_per_unit = value
            self.add_event_to_updated_recipes("Updated kg per unit")
            self._increment_version()

    @property
    def liters_per_kg(self) -> float | None:
        self._check_not_discarded()
        return self._liters_per_kg
    
    def _set_liters_per_kg(self, value: float | None) -> None:
        """Protected setter for liters_per_kg. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._liters_per_kg != value:
            self._liters_per_kg = value
            self.add_event_to_updated_recipes("Updated liters per kg")
            self._increment_version()

    @property
    def nutrition_group(self) -> str | None:
        self._check_not_discarded()
        return self._nutrition_group
    
    def _set_nutrition_group(self, value: str | None) -> None:
        """Protected setter for nutrition_group. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._nutrition_group != value:
            self._nutrition_group = value
            self._increment_version()

    @property
    def cooking_factor(self) -> float | None:
        self._check_not_discarded()
        return self._cooking_factor
    
    def _set_cooking_factor(self, value: float) -> None:
        """Protected setter for cooking_factor. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._cooking_factor != value:
            self._cooking_factor = value
            self.add_event_to_updated_recipes("Updated cooking factor")
            self._increment_version()

    @property
    def conservation_days(self) -> int | None:
        self._check_not_discarded()
        return self._conservation_days
    
    def _set_conservation_days(self, value: int | None) -> None:
        """Protected setter for conservation_days. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._conservation_days != value:
            self._conservation_days = value
            self.add_event_to_updated_recipes("Updated conservation days")
            self._increment_version()

    @property
    def substitutes(self) -> str | None:
        self._check_not_discarded()
        return self._substitutes
    
    def _set_substitutes(self, value: str | None) -> None:
        """Protected setter for substitutes. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._substitutes != value:
            self._substitutes = value
            self.add_event_to_updated_recipes("Updated substitutes")
            self._increment_version()

    @property
    def brand_id(self) -> str | None:
        self._check_not_discarded()
        return self._brand_id

    def _set_brand_id(self, value: str) -> None:
        """Protected setter for brand_id. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._brand_id != value:
            self._brand_id = value
            self._increment_version()

    @property
    def category_id(self) -> str | None:
        self._check_not_discarded()
        return self._category_id

    def _set_category_id(self, value: str) -> None:
        """Protected setter for category_id. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._category_id != value:
            self._category_id = value
            self._increment_version()

    @property
    def parent_category_id(self) -> str | None:
        self._check_not_discarded()
        return self._parent_category_id

    def _set_parent_category_id(self, value: str) -> None:
        """Protected setter for parent_category_id. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._parent_category_id != value:
            self._parent_category_id = value
            self._increment_version()

    @property
    def score(self) -> Score | None:
        self._check_not_discarded()
        return self._score

    def _set_score(self, value: Score | None) -> None:
        """Protected setter for score. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._score != value:
            self._score = value
            self._increment_version()

    @property
    def barcode(self) -> str | None:
        self._check_not_discarded()
        return self._barcode

    @staticmethod
    def is_barcode_unique(barcode: str) -> bool:
        try:
            return len(str(int(barcode if barcode else 0))) > 6
        except Exception:
            return False

    @property
    def food_group_id(self) -> str | None:
        self._check_not_discarded()
        return self._food_group_id

    def _set_food_group_id(self, value: str) -> None:
        """Protected setter for food_group_id. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._food_group_id != value:
            self._food_group_id = value
            self._increment_version()

    @property
    def process_type_id(self) -> str | None:
        self._check_not_discarded()
        return self._process_type_id

    def _set_process_type_id(self, value: str) -> None:
        """Protected setter for process_type_id. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._process_type_id != value:
            self._process_type_id = value
            self._increment_version()

    @property
    def nutri_facts(self) -> NutriFacts | None:
        self._check_not_discarded()
        return self._nutri_facts

    def _set_nutri_facts(self, value: NutriFacts | None) -> None:
        """Protected setter for nutri_facts. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._nutri_facts != value:
            self._nutri_facts = value
            self._increment_version()

    @property
    def ingredients(self) -> str | None:
        self._check_not_discarded()
        return self._ingredients

    def _set_ingredients(self, value: str) -> None:
        """Protected setter for ingredients. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._ingredients != value:
            self._ingredients = value
            self._increment_version()

    @property
    def package_size(self) -> float | None:
        self._check_not_discarded()
        return self._package_size

    def _set_package_size(self, value: float | None) -> None:
        """Protected setter for package_size. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._package_size != value:
            self._package_size = value
            self._increment_version()

    @property
    def package_size_unit(self) -> str | None:
        self._check_not_discarded()
        return self._package_size_unit

    def _set_package_size_unit(self, value: str) -> None:
        """Protected setter for package_size_unit. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._package_size_unit != value:
            self._package_size_unit = value
            self._increment_version()

    @property
    def json_data(self) -> str | None:
        self._check_not_discarded()
        return self._json_data

    def _set_json_data(self, value: str) -> None:
        """Protected setter for json_data. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._json_data != value:
            self._json_data = value
            self._increment_version()

    @property
    def is_food(self) -> bool | None:
        self._check_not_discarded()
        return self._is_food

    def _set_is_food(self, value: bool) -> None:
        """Protected setter for is_food. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._is_food != value:
            self._is_food = value
            self._increment_version()

    @property
    def image_url(self) -> str | None:
        self._check_not_discarded()
        return self._image_url

    def _set_image_url(self, value: str) -> None:
        """Protected setter for image_url. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._image_url != value:
            self._image_url = value
            self._increment_version()

    @property
    def is_food_votes(self) -> IsFoodVotes | None:
        self._check_not_discarded()
        return self._is_food_votes

    @property
    def is_food_houses_choice(self) -> bool | None:
        is_food = len(self._is_food_votes.is_food_houses)
        is_not_food = len(self._is_food_votes.is_not_food_houses)
        total_inputs = is_food + is_not_food
        if not self._is_food_votes.acceptance_line:
            return None
        closest = min(
            self._is_food_votes.acceptance_line.keys(),
            key=lambda x: abs(x - total_inputs),
        )
        if closest > is_food + is_not_food:
            closest_index = list(self._is_food_votes.acceptance_line.keys()).index(
                closest
            )
            closest = self._is_food_votes.acceptance_line.get(closest_index - 1)
        line = self._is_food_votes.acceptance_line.get(closest) if closest else None
        if line is None:
            return None
        if is_food / total_inputs >= line:
            return True
        if is_not_food / total_inputs >= line:
            return False
        return None

    def add_house_input_to_is_food_registry(self, house_id: str, is_food: bool) -> None:
        self._check_not_discarded()
        # initial = self.is_food_houses_choice
        if is_food:
            if house_id in self._is_food_votes.is_food_houses:
                return
            else:
                new_votes = self._is_food_votes.replace(
                    is_food_houses=self._is_food_votes.is_food_houses.union({house_id}),
                    is_not_food_houses=self._is_food_votes.is_not_food_houses.difference({house_id}),
                )
                self._is_food_votes = new_votes
                self._increment_version()
        else:
            if house_id in self._is_food_votes.is_not_food_houses:
                return
            else:
                new_votes = self._is_food_votes.replace(
                    is_food_houses=self._is_food_votes.is_food_houses.difference({house_id}),
                    is_not_food_houses=self._is_food_votes.is_not_food_houses.union({house_id}),
                )
                self._is_food_votes = new_votes
                self._increment_version()
        # final = self.is_food_houses_choice
        # if initial != final:
        #     event = UserIsFoodChoiceChanged(
        #         product_id=self._id,
        #         is_food=self.is_food,
        #         old_choice=initial,
        #         new_choice=final,
        #     )
        #     self.events.append(event)

    def __repr__(self) -> str:
        self._check_not_discarded()
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id!r}, source_id={self.source_id!r}, name={self.name!r}, barcode={self.barcode!r})"
        )

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        """Override to route property updates to protected setter methods."""
        self._check_not_discarded()
        if not kwargs:
            return
        
        # Store original version for single increment (like base Entity class)
        original_version = self.version
        
        # Validate all properties first (similar to Entity base class)
        for key, value in kwargs.items():
            if key[0] == "_":
                raise AttributeError(f"{key} is private.")
            
            # Check if there's a corresponding protected setter method
            setter_method_name = f"_set_{key}"
            if not hasattr(self, setter_method_name):
                raise AttributeError(f"Product has no property '{key}' or it cannot be updated.")
        
        # Apply all property updates using reflection
        for key, value in kwargs.items():
            setter_method = getattr(self, f"_set_{key}")
            setter_method(value)
        
        # Set version manually to avoid multiple increments (like base Entity class)
        self._version = original_version + 1

    def update_properties(self, **kwargs) -> None:
        """Update multiple properties atomically through protected setters."""
        self._check_not_discarded()
        
        # Process properties through _update_properties
        # Event generation is now handled by individual _set_* methods
        if kwargs:
            self._update_properties(**kwargs)
