from pydantic import HttpUrl
import pytest
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.shared_kernel.domain.enums import Privacy

# Import all factory functions
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    # Specialized factory functions

    create_vegetarian_api_recipe,
    create_high_protein_api_recipe,
    create_quick_api_recipe,
    create_dessert_api_recipe,
    create_api_recipe_with_max_fields,
    create_api_recipe_with_incorrect_averages,
    create_api_recipe_without_ratings,
      
    # Helper functions
    create_recipe_collection,
    
    # Helper functions for nested objects
    create_api_nutri_facts,
)

# Import DOMAIN factory functions for proper domain object creation
from tests.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import (
    create_recipe,
    create_complex_recipe as create_complex_domain_recipe
)

# Import ORM factory functions for real ORM instances
from tests.contexts.recipes_catalog.data_factories.meal.recipe.recipe_orm_factories import (
    create_recipe_orm
)

# =============================================================================
# FIXTURES AND TEST DATA
# =============================================================================

@pytest.fixture
def simple_recipe():
    """Simple recipe for basic testing."""
    from uuid import uuid4
    from datetime import datetime, timedelta
    from src.contexts.shared_kernel.domain.enums import MeasureUnit
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
    
    recipe_id = str(uuid4())
    recipe_author_id = str(uuid4())
    user_id = str(uuid4())
    base_time = datetime.now() - timedelta(days=1)
    
    return ApiRecipe(
        id=recipe_id,
        author_id=recipe_author_id,
        meal_id=str(uuid4()),
        name="Simple Toast",
        description="Quick and easy toast with butter",
        instructions="1. Toast bread. 2. Spread butter. 3. Serve.",
        total_time=5,
        ingredients=frozenset([
            ApiIngredient(
                name="Bread",
                quantity=2.0,
                unit=MeasureUnit.SLICE,
                position=0,
                full_text="2 slices bread",
                product_id=None
            ),
            ApiIngredient(
                name="Butter", 
                quantity=1.0,
                unit=MeasureUnit.TABLESPOON,
                position=1,
                full_text="1 tablespoon butter",
                product_id=None
            )
        ]),
        tags=frozenset([
            ApiTag(key="difficulty", value="easy", author_id=recipe_author_id, type="recipe"),
            ApiTag(key="meal-type", value="breakfast", author_id=recipe_author_id, type="recipe")
        ]),
        ratings=frozenset([
            ApiRating(
                user_id=user_id,
                recipe_id=recipe_id,
                taste=3,
                convenience=5,
                comment="Simple but effective"
            )
        ]),
        privacy=Privacy.PUBLIC,
        version=1,
        utensils="Toaster, knife",
        notes="Perfect for quick breakfast",
        nutri_facts=create_api_nutri_facts(
            calories=250.0,
            protein=6.0,
            carbohydrate=30.0,
            total_fat=12.0,
            sodium=400.0
        ),
        weight_in_grams=80,
        image_url=None,
        average_taste_rating=3.0,
        average_convenience_rating=5.0,
        created_at=base_time,
        updated_at=base_time + timedelta(minutes=5),
        discarded=False
    )

@pytest.fixture
def complex_recipe():
    """Complex recipe for advanced testing with nested objects."""
    from uuid import uuid4
    from datetime import datetime, timedelta
    from src.contexts.shared_kernel.domain.enums import MeasureUnit
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
    from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
    from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
    
    recipe_id = str(uuid4())
    recipe_author_id = str(uuid4())
    user_id = str(uuid4())
    base_time = datetime.now() - timedelta(days=2)
    
    # Enhanced ingredients - adding 6th ingredient for test requirement
    ingredients = frozenset([
        ApiIngredient(
            name="Beef Tenderloin",
            quantity=800.0,
            unit=MeasureUnit.GRAM,
            position=0,
            full_text="800g beef tenderloin, trimmed",
            product_id="301b032f-ed2e-476f-8082-dd02b67f28a2"
        ),
        ApiIngredient(
            name="Mushrooms",
            quantity=300.0,
            unit=MeasureUnit.GRAM,
            position=1,
            full_text="300g mixed mushrooms, finely chopped",
            product_id=None
        ),
        ApiIngredient(
            name="Puff Pastry",
            quantity=1.0,
            unit=MeasureUnit.UNIT,
            position=2,
            full_text="1 sheet puff pastry, thawed",
            product_id="a8b60de4-6cb5-4509-ba0a-935f9dfddbeb"
        ),
        ApiIngredient(
            name="Prosciutto",
            quantity=150.0,
            unit=MeasureUnit.GRAM,
            position=3,
            full_text="150g prosciutto, thinly sliced",
            product_id="aa02f531-8b1d-44e0-bce4-c5097656dbbb"
        ),
        ApiIngredient(
            name="Egg",
            quantity=1.0,
            unit=MeasureUnit.UNIT,
            position=4,
            full_text="1 egg, beaten for wash",
            product_id=None
        ),
        ApiIngredient(
            name="Fresh Thyme",
            quantity=2.0,
            unit=MeasureUnit.TABLESPOON,
            position=5,
            full_text="2 tbsp fresh thyme leaves",
            product_id=None
        )
    ])
    
    # Complex ratings
    ratings = frozenset([
        ApiRating(
            user_id=user_id,
            recipe_id=recipe_id,
            taste=5,
            convenience=2,
            comment="Exceptional fine dining experience!"
        ),
        ApiRating(
            user_id=str(uuid4()),
            recipe_id=recipe_id,
            taste=4,
            convenience=2,
            comment="Complex but worth the effort"
        ),
        ApiRating(
            user_id=str(uuid4()),
            recipe_id=recipe_id,
            taste=4,
            convenience=2,
            comment="Restaurant quality at home"
        )
    ])
    
    # Complex tags  
    tags = frozenset([
        ApiTag(key="category", value="beef", author_id=recipe_author_id, type="recipe"),
        ApiTag(key="style", value="fine-dining", author_id=recipe_author_id, type="recipe"),
        ApiTag(key="cuisine", value="french", author_id=recipe_author_id, type="recipe"),
        ApiTag(key="technique", value="pastry", author_id=recipe_author_id, type="recipe")
    ])
    
    # Complex nutrition facts
    nutri_facts = create_api_nutri_facts()
    
    return ApiRecipe(
        id=recipe_id,
        author_id=recipe_author_id,
        meal_id=str(uuid4()),
        name="Beef Wellington with Mushroom Duxelles",
        description="Classic French dish with beef tenderloin wrapped in pâté, mushroom duxelles, and puff pastry.",
        instructions="1. Sear beef tenderloin on all sides. 2. Prepare mushroom duxelles by sautéing mushrooms until moisture evaporates. 3. Wrap beef in plastic with duxelles, chill 30 minutes. 4. Roll out puff pastry. 5. Wrap beef in pastry, seal edges. 6. Egg wash and score. 7. Bake at 400°F for 25-30 minutes. 8. Rest 10 minutes before slicing.",
        total_time=180,
        ingredients=ingredients,
        tags=tags,
        ratings=ratings,
        privacy=Privacy.PUBLIC,
        version=1,
        utensils="Roasting pan, pastry brush, plastic wrap, chef's knife",
        notes="Temperature control is crucial - use meat thermometer for perfect doneness.",
        nutri_facts=nutri_facts,
        weight_in_grams=1200,
        image_url=HttpUrl("https://example.com/beef-wellington.jpg"),
        average_taste_rating=4.33,
        average_convenience_rating=2.0,
        created_at=base_time,
        updated_at=base_time + timedelta(hours=2),
        discarded=False
    )

@pytest.fixture
def domain_recipe():
    """Domain recipe for conversion tests - created directly from domain factories."""
    return create_recipe()

@pytest.fixture
def domain_recipe_with_nutri_facts():
    """Domain recipe with nutrition facts for nutrition conversion tests."""
    return create_complex_domain_recipe()

@pytest.fixture
def real_orm_recipe():
    """Real ORM recipe for testing - no mocks needed."""
    return create_recipe_orm(
        name="Test Recipe for ORM Conversion",
        description="Real ORM recipe for testing conversion methods",
        instructions="Real instructions for testing",
        author_id=str(uuid4()),
        meal_id=str(uuid4())
    )

@pytest.fixture
def edge_case_recipes():
    """Collection of edge case recipes for comprehensive testing."""
    from uuid import uuid4
    from datetime import datetime, timedelta
    
    # Create explicit minimal recipe (replaces create_minimal_api_recipe)
    minimal_recipe_id = str(uuid4())
    minimal_author_id = str(uuid4())
    minimal_base_time = datetime.now() - timedelta(days=3)
    
    minimal_recipe = ApiRecipe(
        id=minimal_recipe_id,
        author_id=minimal_author_id,
        meal_id=str(uuid4()),
        name="Minimal Recipe",
        description="Basic recipe with minimal fields",
        instructions="Do the thing.",
        total_time=1,
        ingredients=frozenset(),
        tags=frozenset(),
        ratings=frozenset(),
        privacy=Privacy.PUBLIC,
        version=1,
        utensils="None",
        notes="Minimal test case",
        nutri_facts=None,
        weight_in_grams=0,
        image_url=None,
        average_taste_rating=None,
        average_convenience_rating=None,
        created_at=minimal_base_time,
        updated_at=minimal_base_time,
        discarded=False
    )
    
    return {
        "empty_collections": minimal_recipe,
        "max_fields": create_api_recipe_with_max_fields(),  # Keep complex factory
        "incorrect_averages": create_api_recipe_with_incorrect_averages(),  # Keep for edge case testing
        "no_ratings": create_api_recipe_without_ratings(),  # Keep for specific testing
        "vegetarian": create_vegetarian_api_recipe(),  # Keep specialized factory
        "high_protein": create_high_protein_api_recipe(),  # Keep specialized factory
        "quick": create_quick_api_recipe(),  # Keep specialized factory
        "dessert": create_dessert_api_recipe()  # Keep specialized factory
    }

@pytest.fixture
def recipe_collection():
    """Collection of diverse recipes for batch testing."""
    return create_recipe_collection(count=10) 