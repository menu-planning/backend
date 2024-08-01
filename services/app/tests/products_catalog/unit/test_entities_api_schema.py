import pytest
from attrs import asdict
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.value_objects.score import (
    ApiScore,
)
from src.contexts.products_catalog.shared.adapters.repositories.product import (
    ProductRepo,
)
from src.contexts.products_catalog.shared.domain.value_objects.score import Score
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from tests.products_catalog.random_refs import (
    random_barcode,
    random_food_product,
    random_nutri_facts,
    random_score_kwargs,
)


class TestApiNutriFacts:
    def test_api_nutri_facts(self) -> None:
        nutri_facts = random_nutri_facts()
        kwargs = asdict(nutri_facts)
        api = ApiNutriFacts(**kwargs)
        domain = api.to_domain()
        assert domain == nutri_facts
        assert ApiNutriFacts.from_domain(domain) == api

    def test_negative_values(self) -> None:
        nutri_facts = random_nutri_facts()
        kwargs = asdict(nutri_facts)
        kwargs["calories"]["value"] = -1
        with pytest.raises(ValueError):
            ApiNutriFacts(**kwargs)


class TestApiScore:
    def test_api_score(self) -> None:
        score = random_score_kwargs()
        api = ApiScore(**score)
        domain = api.to_domain()
        assert domain == Score(**score)
        assert ApiScore.from_domain(domain) == api

    def test_negative_values(self) -> None:
        score = random_score_kwargs()
        score["nutrients"] = -1
        with pytest.raises(ValueError):
            ApiScore(**score)

    def test_over_100_values(self) -> None:
        score = random_score_kwargs()
        score["nutrients"] = 101
        with pytest.raises(ValueError):
            ApiScore(**score)


class TestApiProduct:
    def test_api_product(self) -> None:
        product = random_food_product(barcode=random_barcode())
        api = ApiProduct.from_domain(product)
        domain = api.to_domain()
        assert domain == product
        assert api == ApiProduct.from_domain(domain)


class TestApiFilter:
    def test_api_filters_match_repository_filters(self) -> None:
        mappers = ProductRepo.filter_to_column_mappers
        generic_filters = SaGenericRepository.ALLOWED_FILTERS
        filters = []
        for mapper in mappers:
            filters.extend(list(mapper.filter_key_to_column_name.keys()))

        filters.extend(generic_filters)
        api_filters = ApiProductFilter.model_fields.keys()
        processed_api_filters = []
        for k in api_filters:
            processed_api_filters.append(SaGenericRepository.removePostfix(k))
        assert set(filters) == set(processed_api_filters)
