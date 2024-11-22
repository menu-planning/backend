from sqlalchemy import inspect
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.meal.meal import (
    MealMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import (
    MealSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import (
    StrProcessor,
)
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from tests.recipes_catalog.random_refs import (
    random_create_recipe_on_meal_kwargs,
    random_meal,
)


def test_CANNOT_map_where_children_have_refences_by_ids():
    mapper = MealMapper()
    domain = random_meal()
    create_recipe_on_meal_kwargs = random_create_recipe_on_meal_kwargs()
    domain.create_recipe(**create_recipe_on_meal_kwargs)
    sa_model = mapper.map_domain_to_sa(domain)
    domain2 = mapper.map_sa_to_domain(sa_model)
    assert domain.recipes[0].diet_types_ids != domain2.recipes[0].diet_types_ids
    assert domain.recipes[0].meal_planning_ids != domain2.recipes[0].meal_planning_ids


async def test_if_sa_model_relationship_name_match_domain_model_attribute_name():
    inspector = inspect(MealSaModel)
    for attribute in inspector.relationships.keys():
        assert (
            attribute in dir(Meal)
            or attribute + "_id" in dir(Meal)
            or attribute + "_ids" in dir(Meal)
        )
