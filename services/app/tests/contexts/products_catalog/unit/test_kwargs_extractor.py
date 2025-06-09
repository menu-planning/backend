import pytest
from attrs import asdict
from src.contexts.products_catalog.core.adapters.product_kwargs_extractor import (
    ProductKwargsExtractorFactory,
)
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from tests.products_catalog.random_refs import random_barcode, random_food_product


class TestPrivate:
    @pytest.mark.skip()
    def test_single_str_value(self):
        # TODO: Implement this test
        pass
        products: list[Product] = []
        products_data = []
        n = 10
        for _ in range(n):
            p = random_food_product(prefix="e2e_get_products", barcode=random_barcode())
            products.append(p)
            products_data.append(
                {
                    "name": p.name,
                    "parent_category": p.parent_category_id,
                    "category": p.category_id,
                    "brands": [p.brand, "brand2"],
                    "barcode": p.barcode,
                    "ingredients_text": p.ingredients,
                    "package_size": p.package_size,
                    "package_size_unit": p.package_size_unit,
                    "score": {
                        "final": p.score.final if p.score else None,
                        "nutrients": p.score.nutrients if p.score else None,
                        "ingredients": p.score.ingredients if p.score else None,
                    },
                    "nutrition_facts": {
                        k: v["value"] for k, v in asdict(p.nutri_facts).items()
                    },
                },
            )
        kwargs_extractor = ProductKwargsExtractorFactory().get_extractor(
            source="private"
        )
        extractor = kwargs_extractor(products_data)
        products_kwargs = extractor.kwargs
        assert len(products_kwargs) == n
        assert all([p.name == kw["name"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [
                p.parent_category_id == kw["parent_category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.category_id == kw["category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all([p.brand == kw["brand"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [p.barcode == kw["barcode"] for p, kw in zip(products, products_kwargs)]
        )
        assert all(
            [
                p.ingredients == kw["ingredients"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.package_size == kw["package_size"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.package_size_unit == kw["package_size_unit"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        for p, kw in zip(products, products_kwargs):
            assert all(
                [
                    (p.score is None and kw["score"] is None)
                    or (
                        asdict(p.score)[s] == kw["score"][a]
                        for s, a in zip(asdict(p.score).keys(), kw["score"].keys())
                    )
                ]
            )
        for p, kw in zip(products, products_kwargs):
            assert all(
                [
                    (p.nutri_facts is None and kw["nutri_facts"] is None)
                    or (
                        asdict(p.nutri_facts)[s]["value"] == kw["nutri_facts"][a]
                        for s, a in zip(
                            asdict(p.nutri_facts).keys(), kw["nutri_facts"].keys()
                        )
                    )
                ]
            )

    @pytest.mark.skip()
    def test_barcode_inside_list_value(self):
        # TODO: Implement this test
        pass
        products: list[Product] = []
        products_data = []
        n = 10
        for _ in range(n):
            p = random_food_product(prefix="e2e_get_products", barcode=random_barcode())
            products.append(p)
            products_data.append(
                {
                    "name": p.name,
                    "parent_category": p.parent_category_id,
                    "category": p.category_id,
                    "brands": [p.brand, "brand2"],
                    "barcode": [p.barcode],
                    "ingredients_text": p.ingredients,
                    "package_size": p.package_size,
                    "package_size_unit": p.package_size_unit,
                    "score": {
                        "final": p.score.final if p.score else None,
                        "nutrients": p.score.nutrients if p.score else None,
                        "ingredients": p.score.ingredients if p.score else None,
                    },
                    "nutrition_facts": {
                        k: v["value"] for k, v in asdict(p.nutri_facts).items()
                    },
                },
            )
        kwargs_extractor = ProductKwargsExtractorFactory().get_extractor(
            source="private"
        )
        extractor = kwargs_extractor(products_data)
        products_kwargs = extractor.kwargs
        assert len(products_kwargs) == n
        assert all([p.name == kw["name"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [
                p.parent_category_id == kw["parent_category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.category_id == kw["category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all([p.brand == kw["brand"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [p.barcode == kw["barcode"] for p, kw in zip(products, products_kwargs)]
        )
        assert all(
            [
                p.ingredients == kw["ingredients"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.package_size == kw["package_size"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.package_size_unit == kw["package_size_unit"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        for p, kw in zip(products, products_kwargs):
            assert all(
                [
                    (p.score is None and kw["score"] is None)
                    or (
                        asdict(p.score)[s] == kw["score"][a]
                        for s, a in zip(asdict(p.score).keys(), kw["score"].keys())
                    )
                ]
            )
        for p, kw in zip(products, products_kwargs):
            assert all(
                [
                    (p.nutri_facts is None and kw["nutri_facts"] is None)
                    or (
                        asdict(p.nutri_facts)[s]["value"] == kw["nutri_facts"][a]
                        for s, a in zip(
                            asdict(p.nutri_facts).keys(), kw["nutri_facts"].keys()
                        )
                    )
                ]
            )

    @pytest.mark.skip()
    def test_normalize_nutri_facts_to_base_100(self):
        # TODO: Implement this test
        pass
        products: list[Product] = []
        products_data = []
        serving_size = 5
        n = 10
        for _ in range(n):
            p = random_food_product(prefix="e2e_get_products", barcode=random_barcode())
            products.append(p)
            products_data.append(
                {
                    "name": p.name,
                    "parent_category": p.parent_category_id,
                    "category": p.category_id,
                    "brands": [p.brand, "brand2"],
                    "barcode": [p.barcode],
                    "ingredients_text": p.ingredients,
                    "package_size": p.package_size,
                    "package_size_unit": p.package_size_unit,
                    "score": {
                        "final": p.score.final if p.score else None,
                        "nutrients": p.score.nutrients if p.score else None,
                        "ingredients": p.score.ingredients if p.score else None,
                    },
                    "nutrition_facts": {
                        k: v["value"] for k, v in asdict(p.nutri_facts).items()
                    }
                    | {"serving_size": serving_size},
                },
            )
        kwargs_extractor = ProductKwargsExtractorFactory().get_extractor(
            source="private"
        )
        extractor = kwargs_extractor(products_data)
        products_kwargs = extractor.kwargs
        assert len(products_kwargs) == n
        assert all([p.name == kw["name"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [
                p.parent_category_id == kw["parent_category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.category_id == kw["category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all([p.brand == kw["brand"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [p.barcode == kw["barcode"] for p, kw in zip(products, products_kwargs)]
        )
        assert all(
            [
                p.ingredients == kw["ingredients"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.package_size == kw["package_size"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.package_size_unit == kw["package_size_unit"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        for p, kw in zip(products, products_kwargs):
            assert all(
                [
                    (p.score is None and kw["score"] is None)
                    or (
                        asdict(p.score)[s] == kw["score"][a]
                        for s, a in zip(asdict(p.score).keys(), kw["score"].keys())
                    )
                ]
            )
        normalizer = serving_size / 100
        for p, kw in zip(products, products_kwargs):
            assert all(
                [
                    (p.nutri_facts is None and kw["nutri_facts"] is None)
                    or (
                        asdict(p.nutri_facts)[s]["value"] / normalizer
                        == kw["nutri_facts"][a]
                        for s, a in zip(
                            asdict(p.nutri_facts).keys(), kw["nutri_facts"].keys()
                        )
                    )
                ]
            )


class TestTaco:
    def test_all_values(self):
        products: list[Product] = []
        products_data = []
        n = 10
        for _ in range(n):
            p = random_food_product(
                prefix="e2e_get_products",
            )
            products.append(p)
            products_data.append(
                {
                    "id": 274,
                    "description": p.name,
                    "vitaminC": {"qty": p.nutri_facts.vitamin_c.value, "unit": "mg"},
                    "re": {"qty": "Tr", "unit": "mcg"},
                    "rae": {"qty": "Tr", "unit": "mcg"},
                    "base_qty": 100,
                    "base_unit": "g",
                    "category_id": p.category_id,
                    "attributes": {
                        "carbohydrate": {
                            "qty": p.nutri_facts.carbohydrate.value,
                            "unit": "g",
                        },
                        "humidity": {"qty": 79.7336666666667, "unit": "percents"},
                        "protein": {"qty": p.nutri_facts.protein.value, "unit": "g"},
                        "lipid": {"qty": p.nutri_facts.total_fat.value, "unit": "g"},
                        "cholesterol": {
                            "qty": p.nutri_facts.cholesterol.value,
                            "unit": "mg",
                        },
                        "fiber": {
                            "qty": p.nutri_facts.dietary_fiber.value,
                            "unit": "g",
                        },
                        "ashes": {"qty": p.nutri_facts.ashes.value, "unit": "g"},
                        "calcium": {"qty": p.nutri_facts.calcium.value, "unit": "mg"},
                        "magnesium": {
                            "qty": p.nutri_facts.magnesium.value,
                            "unit": "mg",
                        },
                        "phosphorus": {
                            "qty": p.nutri_facts.phosphorus.value,
                            "unit": "mg",
                        },
                        "iron": {"qty": p.nutri_facts.iron.value, "unit": "mg"},
                        "sodium": {"qty": p.nutri_facts.sodium.value, "unit": "mg"},
                        "potassium": {
                            "qty": p.nutri_facts.potassium.value,
                            "unit": "mg",
                        },
                        "copper": {"qty": p.nutri_facts.copper.value, "unit": "mg"},
                        "zinc": {"qty": p.nutri_facts.zinc.value, "unit": "mg"},
                        "retinol": {"qty": p.nutri_facts.retinol.value, "unit": "mcg"},
                        "thiamine": {"qty": p.nutri_facts.thiamine.value, "unit": "mg"},
                        "riboflavin": {
                            "qty": p.nutri_facts.riboflavin.value,
                            "unit": "mg",
                        },
                        "pyridoxine": {
                            "qty": p.nutri_facts.pyridoxine.value,
                            "unit": "mg",
                        },
                        "niacin": {"qty": p.nutri_facts.niacin.value, "unit": "mg"},
                        "energy": {
                            "kcal": p.nutri_facts.calories.value,
                            "kj": 381.177246486999,
                        },
                        "fatty_acids": {
                            "saturated": {
                                "qty": p.nutri_facts.saturated_fat.value,
                                "unit": "g",
                            },
                            "monounsaturated": {
                                "qty": p.nutri_facts.monounsaturated_fat.value,
                                "unit": "g",
                            },
                            "polyunsaturated": {
                                "qty": p.nutri_facts.polyunsaturated_fat.value,
                                "unit": "g",
                            },
                            "14:0": {"qty": "Tr", "unit": "g"},
                            "16:0": {"qty": 0.288333333333333, "unit": "g"},
                            "18:0": {"qty": 0.081333333333333, "unit": "g"},
                            "16:1": {"qty": 0.011333333333333, "unit": "g"},
                            "18:1": {
                                "qty": p.nutri_facts.oleic_acid.value,
                                "unit": "g",
                            },
                            "20:1": {"qty": 0.015333333333333, "unit": "g"},
                            "18:2 n-6": {
                                "qty": p.nutri_facts.linoleic_acid.value,
                                "unit": "g",
                            },
                            "20:4": {"qty": "Tr", "unit": "g"},
                            "20:5": {"qty": p.nutri_facts.epa.value, "unit": "g"},
                            "22:5": {"qty": "Tr", "unit": "g"},
                            "22:6": {"qty": p.nutri_facts.dha.value, "unit": "g"},
                        },
                        "manganese": {
                            "qty": p.nutri_facts.manganese.value,
                            "unit": "mg",
                        },
                    },
                }
            )
        kwargs_extractor = ProductKwargsExtractorFactory().get_extractor(source="taco")
        extractor = kwargs_extractor(products_data)
        products_kwargs = extractor.kwargs
        assert len(products_kwargs) == n
        assert all([p.name == kw["name"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [
                p.category_id == kw["parent_category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.category_id == kw["category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(["" == kw["brand"] for kw in products_kwargs])
        assert all(["" == kw["barcode"] for kw in products_kwargs])
        assert all([kw["ingredients"] is None for kw in products_kwargs])
        assert all(["" == kw["package_size"] for kw in products_kwargs])
        assert all(["g" == kw["package_size_unit"] for kw in products_kwargs])
        for i in [(p, kw) for p, kw in zip(products, products_kwargs)]:
            assert i[0].nutri_facts.protein.value == i[1]["nutri_facts"]["protein"]
            assert i[0].nutri_facts.total_fat.value == i[1]["nutri_facts"]["total_fat"]
            assert (
                i[0].nutri_facts.cholesterol.value == i[1]["nutri_facts"]["cholesterol"]
            )
            assert i[0].nutri_facts.ashes.value == i[1]["nutri_facts"]["ashes"]
            assert i[0].nutri_facts.calcium.value == i[1]["nutri_facts"]["calcium"]
            assert i[0].nutri_facts.magnesium.value == i[1]["nutri_facts"]["magnesium"]
            assert (
                i[0].nutri_facts.phosphorus.value == i[1]["nutri_facts"]["phosphorus"]
            )
            assert i[0].nutri_facts.iron.value == i[1]["nutri_facts"]["iron"]
            assert i[0].nutri_facts.sodium.value == i[1]["nutri_facts"]["sodium"]
            assert i[0].nutri_facts.potassium.value == i[1]["nutri_facts"]["potassium"]
            assert i[0].nutri_facts.copper.value == i[1]["nutri_facts"]["copper"]
            assert i[0].nutri_facts.zinc.value == i[1]["nutri_facts"]["zinc"]
            assert (
                i[0].nutri_facts.saturated_fat.value
                == i[1]["nutri_facts"]["saturated_fat"]
            )
            assert (
                i[0].nutri_facts.monounsaturated_fat.value
                == i[1]["nutri_facts"]["monounsaturated_fat"]
            )
            assert (
                i[0].nutri_facts.polyunsaturated_fat.value
                == i[1]["nutri_facts"]["polyunsaturated_fat"]
            )
            assert (
                i[0].nutri_facts.oleic_acid.value == i[1]["nutri_facts"]["oleic_acid"]
            )
            assert (
                i[0].nutri_facts.linoleic_acid.value
                == i[1]["nutri_facts"]["linoleic_acid"]
            )
            assert i[0].nutri_facts.epa.value == i[1]["nutri_facts"]["epa"]
            assert i[0].nutri_facts.dha.value == i[1]["nutri_facts"]["dha"]
            assert i[0].nutri_facts.calories.value == i[1]["nutri_facts"]["calories"]
            assert (
                i[0].nutri_facts.carbohydrate.value
                == i[1]["nutri_facts"]["carbohydrate"]
            )
            assert (
                i[0].nutri_facts.dietary_fiber.value
                == i[1]["nutri_facts"]["dietary_fiber"]
            )

    def test_missing_values(self):
        products: list[Product] = []
        products_data = []
        n = 10
        for _ in range(n):
            p = random_food_product(
                prefix="e2e_get_products",
            )
            products.append(p)
            products_data.append(
                {
                    "id": 274,
                    "description": p.name,
                    "re": {"qty": "Tr", "unit": "mcg"},
                    "rae": {"qty": "Tr", "unit": "mcg"},
                    "base_qty": 100,
                    "base_unit": "g",
                    "category_id": p.category_id,
                    "attributes": {
                        # "carbohydrate": {
                        #     "qty": p.nutri_facts.carbohydrate,
                        #     "unit": "g",
                        # },
                        "humidity": {"qty": 79.7336666666667, "unit": "percents"},
                        "protein": {"qty": "Tr", "unit": "g"},
                        "lipid": {"qty": "NA", "unit": "g"},
                        "cholesterol": {"qty": "Tr", "unit": "mg"},
                        "fiber": {"qty": "Tr", "unit": "g"},
                        "ashes": {"qty": "Tr", "unit": "g"},
                        "calcium": {"qty": "Tr", "unit": "mg"},
                        "magnesium": {"qty": "Tr", "unit": "mg"},
                        "phosphorus": {"qty": "Tr", "unit": "mg"},
                        "iron": {"qty": "NA", "unit": "mg"},
                        "sodium": {"qty": "Tr", "unit": "mg"},
                        "potassium": {"qty": "Tr", "unit": "mg"},
                        "copper": {"qty": "Tr", "unit": "mg"},
                        "zinc": {"qty": "Tr", "unit": "mg"},
                        "retinol": {"qty": "NA", "unit": "mcg"},
                        "thiamine": {"qty": "", "unit": "mg"},
                        "riboflavin": {"qty": "", "unit": "mg"},
                        "pyridoxine": {"qty": "", "unit": "mg"},
                        "niacin": {"qty": "Tr", "unit": "mg"},
                        "energy": {
                            "kcal": "Tr",
                            "kj": 381.177246486999,
                        },
                        "fatty_acids": {
                            "saturated": {
                                "qty": "Tr",
                                "unit": "g",
                            },
                            "monounsaturated": {
                                "qty": "Tr",
                                "unit": "g",
                            },
                            "polyunsaturated": {
                                "qty": "Tr",
                                "unit": "g",
                            },
                            "14:0": {"qty": "Tr", "unit": "g"},
                            "16:0": {"qty": 0.288333333333333, "unit": "g"},
                            "18:0": {"qty": 0.081333333333333, "unit": "g"},
                            "16:1": {"qty": 0.011333333333333, "unit": "g"},
                            "18:1": {"qty": "Tr", "unit": "g"},
                            "20:1": {"qty": 0.015333333333333, "unit": "g"},
                            "18:2 n-6": {
                                "qty": "Tr",
                                "unit": "g",
                            },
                            "20:4": {"qty": "Tr", "unit": "g"},
                            "20:5": {"qty": "Tr", "unit": "g"},
                            "22:5": {"qty": "Tr", "unit": "g"},
                            "22:6": {"qty": "Tr", "unit": "g"},
                        },
                        "manganese": {"qty": "Tr", "unit": "mg"},
                    },
                }
            )
        kwargs_extractor = ProductKwargsExtractorFactory().get_extractor(source="taco")
        extractor = kwargs_extractor(products_data)
        products_kwargs = extractor.kwargs
        assert len(products_kwargs) == n
        assert all([p.name == kw["name"] for p, kw in zip(products, products_kwargs)])
        assert all(
            [
                p.category_id == kw["parent_category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(
            [
                p.category_id == kw["category"]
                for p, kw in zip(products, products_kwargs)
            ]
        )
        assert all(["" == kw["brand"] for kw in products_kwargs])
        assert all(["" == kw["barcode"] for kw in products_kwargs])
        assert all([kw["ingredients"] is None for kw in products_kwargs])
        assert all(["" == kw["package_size"] for kw in products_kwargs])
        assert all(["g" == kw["package_size_unit"] for kw in products_kwargs])
        for i in [(p, kw) for p, kw in zip(products, products_kwargs)]:
            assert 0 == i[1]["nutri_facts"]["protein"]
            assert 0 == i[1]["nutri_facts"]["total_fat"]
            assert 0 == i[1]["nutri_facts"]["cholesterol"]
            assert 0 == i[1]["nutri_facts"]["ashes"]
            assert 0 == i[1]["nutri_facts"]["calcium"]
            assert 0 == i[1]["nutri_facts"]["magnesium"]
            assert 0 == i[1]["nutri_facts"]["phosphorus"]
            assert 0 == i[1]["nutri_facts"]["iron"]
            assert 0 == i[1]["nutri_facts"]["sodium"]
            assert 0 == i[1]["nutri_facts"]["potassium"]
            assert 0 == i[1]["nutri_facts"]["copper"]
            assert 0 == i[1]["nutri_facts"]["zinc"]
            assert 0 == i[1]["nutri_facts"]["saturated_fat"]
            assert 0 == i[1]["nutri_facts"]["monounsaturated_fat"]
            assert 0 == i[1]["nutri_facts"]["polyunsaturated_fat"]
            assert 0 == i[1]["nutri_facts"]["oleic_acid"]
            assert 0 == i[1]["nutri_facts"]["linoleic_acid"]
            assert 0 == i[1]["nutri_facts"]["epa"]
            assert 0 == i[1]["nutri_facts"]["dha"]
            assert 0 == i[1]["nutri_facts"]["calories"]
            assert 0 == i[1]["nutri_facts"]["carbohydrate"]
            assert 0 == i[1]["nutri_facts"]["dietary_fiber"]
