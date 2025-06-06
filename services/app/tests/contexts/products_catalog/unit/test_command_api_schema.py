from attrs import asdict
from src.contexts.products_catalog.core.adapters.api_schemas.commands.products.add_food_product import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from tests.products_catalog.random_refs import (
    random_attr,
    random_nutri_facts,
    random_score_kwargs,
)


class TestApiAddNewFoodProduct:
    def test_api_add_new_product_cmd(self) -> None:
        nutri_facts = random_nutri_facts()
        nutri_facts_kwargs = asdict(nutri_facts)
        score_kwargs = random_score_kwargs()
        api = ApiAddFoodProduct(
            source_id="private",
            name=random_attr("name"),
            nutri_facts=nutri_facts_kwargs,
            score=score_kwargs,
        )
        domain = api.to_domain()
        assert domain.source_id == api.source_id
        assert domain.name == api.name
        assert domain.nutri_facts == NutriFacts(**nutri_facts_kwargs)
        assert domain.score == Score(**score_kwargs)
