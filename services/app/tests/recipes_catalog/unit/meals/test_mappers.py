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
from tests.recipes_catalog.random_refs import random_meal


def test_map_Meal_to_MealSaModel_back_to_Meal():
    mapper = MealMapper()
    domain = random_meal()
    sa_model = mapper.map_domain_to_sa(domain)
    domain2 = mapper.map_sa_to_domain(sa_model)
    assert domain.id == domain2.id
    assert domain.name == domain2.name
    assert domain.author_id == domain2.author_id
    assert len(domain.recipes) > 0
    assert domain.recipes == domain2.recipes
    assert domain.menu_id == domain2.menu_id
    assert domain.description == domain2.description
    assert domain.notes == domain2.notes
    assert domain.image_url == domain2.image_url
    assert domain.created_at == domain2.created_at
    assert domain.updated_at == domain2.updated_at
    assert domain.discarded == domain2.discarded
    assert domain.version == domain2.version
    assert sa_model.preprocessed_name == StrProcessor(domain.name).output


async def test_if_sa_model_relationship_name_match_domain_model_attribute_name():
    inspector = inspect(MealSaModel)
    for attribute in inspector.relationships.keys():
        assert (
            attribute in dir(Meal)
            or attribute + "_id" in dir(Meal)
            or attribute + "_ids" in dir(Meal)
        )
