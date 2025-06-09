import pytest
from attrs import asdict
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import ApiSource
from src.contexts.products_catalog.core.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.entities.product_filter import (
    ApiProductFilter,
)
from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_score import (
    ApiScore,
)
from src.contexts.products_catalog.core.adapters.repositories.product_repository import (
    ProductRepo,
)
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from tests.products_catalog.random_refs import (
    random_barcode,
    random_food_product,
    random_nutri_facts,
    random_score_kwargs,
    random_source,
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
            processed_api_filters.append(SaGenericRepository.remove_postfix(k))
        assert set(filters) == set(processed_api_filters)

class TestApiSource:
    def test_api_source(self) -> None:
        domain = random_source()
        api = ApiSource.from_domain(domain)
        back_to_domain = api.to_domain()
        assert domain.id == back_to_domain.id
        assert domain.name == back_to_domain.name
        assert domain.description == back_to_domain.description
        assert domain.created_at == back_to_domain.created_at
        assert domain.updated_at == back_to_domain.updated_at
        assert domain.discarded == back_to_domain.discarded
        assert domain.version == back_to_domain.version