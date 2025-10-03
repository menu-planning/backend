from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field
from fastapi import FastAPI

app = FastAPI()

class Child(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(
        # SECURITY & INTEGRITY SETTINGS
        frozen=True,  # Prevents accidental mutation
        extra="forbid",  # Prevents injection attacks
        validate_assignment=True,  # Ensures consistency after creation
        # CONVERSION & COMPATIBILITY SETTINGS
        from_attributes=True,  # Enables ORM integration
        populate_by_name=True,  # Supports multiple naming
        # VALIDATION BEHAVIOR SETTINGS
        validate_default=True,  # Ensures defaults are correct
        str_strip_whitespace=True,  # Data cleansing
        # SERIALIZATION SETTINGS
        alias_generator=None,  # Can be overridden in subclasses for custom naming
        # PERFORMANCE SETTINGS
        arbitrary_types_allowed=False,  # Forces explicit validation
        revalidate_instances="never",  # Performance optimization for immutable objects
    )

class Parent(BaseModel):
    children: Annotated[
            frozenset[Child] | None,
            Field(default_factory=frozenset),
        ]

    model_config = ConfigDict(
        # SECURITY & INTEGRITY SETTINGS
        frozen=True,  # Prevents accidental mutation
        extra="forbid",  # Prevents injection attacks
        validate_assignment=True,  # Ensures consistency after creation
        # CONVERSION & COMPATIBILITY SETTINGS
        from_attributes=True,  # Enables ORM integration
        populate_by_name=True,  # Supports multiple naming
        # VALIDATION BEHAVIOR SETTINGS
        validate_default=True,  # Ensures defaults are correct
        str_strip_whitespace=True,  # Data cleansing
        # SERIALIZATION SETTINGS
        alias_generator=None,  # Can be overridden in subclasses for custom naming
        # PERFORMANCE SETTINGS
        arbitrary_types_allowed=False,  # Forces explicit validation
        revalidate_instances="never",  # Performance optimization for immutable objects
    )

@app.post("/test")
def test(test_model: Parent):
    print(test_model)
    return test_model.children

data = {
    "id": "8516a3d072374175945b4a4e99836f68",
    "name": "Abacate com sal",
    "ingredients": [
      {
        "name": "Abacate",
        "unit": "g",
        "quantity": 150,
        "position": 0,
        "full_text": None,
        "product_id": "82e85ba95c8945ff829e00ca328fc874"
      },
      {
        "name": "Sal",
        "unit": "g",
        "quantity": 1,
        "position": 1,
        "full_text": None,
        "product_id": "d3a43a3e-03d6-422c-a591-a1bade112848"
      }
    ],
    "instructions": "[{\"insert\":\"descascar e cortar\\n\"}]",
    "author_id": "a39cbaea-2031-7081-e1b8-76f4cabda1b3",
    "meal_id": "31852e172b7f492eb11429fdea403ed9",
    "description": None,
    "utensils": None,
    "total_time": None,
    "notes": "",
    "tags": [],
    "privacy": "private",
    "ratings": [],
    "nutri_facts": {
      "calories": {
        "value": 144.2320630434783,
        "unit": "kcal"
      },
      "protein": {
        "value": 1.858695652173915,
        "unit": "g"
      },
      "carbohydrate": {
        "value": 9.0463043478261,
        "unit": "g"
      },
      "total_fat": {
        "value": 12.595000000000004,
        "unit": "g"
      },
      "saturated_fat": {
        "value": 3.45,
        "unit": "g"
      },
      "trans_fat": {
        "value": 0,
        "unit": "g"
      },
      "dietary_fiber": {
        "value": 9.469999999999995,
        "unit": "g"
      },
      "sodium": {
        "value": 399.43,
        "unit": "mg"
      },
      "arachidonic_acid": {
        "value": 0,
        "unit": "g"
      },
      "ashes": {
        "value": 1.8160000000000003,
        "unit": "g"
      },
      "dha": {
        "value": 0,
        "unit": "mg"
      },
      "epa": {
        "value": 0,
        "unit": "mg"
      },
      "sugar": {
        "value": 0,
        "unit": "g"
      },
      "starch": {
        "value": 0,
        "unit": "mcg"
      },
      "biotin": {
        "value": 0,
        "unit": "mcg"
      },
      "boro": {
        "value": 0,
        "unit": "mg"
      },
      "caffeine": {
        "value": 0,
        "unit": "mg"
      },
      "calcium": {
        "value": 12.114000000000006,
        "unit": "mg"
      },
      "chlorine": {
        "value": 0,
        "unit": "mg"
      },
      "copper": {
        "value": 0.2203000000000005,
        "unit": "mg"
      },
      "cholesterol": {
        "value": 0,
        "unit": "mg"
      },
      "choline": {
        "value": 0,
        "unit": "mg"
      },
      "chrome": {
        "value": 0,
        "unit": "mcg"
      },
      "dextrose": {
        "value": 0,
        "unit": "g"
      },
      "sulfur": {
        "value": 0,
        "unit": "mg"
      },
      "phenylalanine": {
        "value": 0,
        "unit": "g"
      },
      "iron": {
        "value": 0.3133000000000005,
        "unit": "mg"
      },
      "insoluble_fiber": {
        "value": 0,
        "unit": "g"
      },
      "soluble_fiber": {
        "value": 0,
        "unit": "g"
      },
      "fluor": {
        "value": 0,
        "unit": "mg"
      },
      "phosphorus": {
        "value": 32.92999999999995,
        "unit": "mg"
      },
      "fructo_oligosaccharides": {
        "value": 0,
        "unit": "mg"
      },
      "fructose": {
        "value": 0,
        "unit": "g"
      },
      "galacto_oligosaccharides": {
        "value": 0,
        "unit": "g"
      },
      "galactose": {
        "value": 0,
        "unit": "mg"
      },
      "glucose": {
        "value": 0,
        "unit": "g"
      },
      "glucoronolactone": {
        "value": 0,
        "unit": "mg"
      },
      "monounsaturated_fat": {
        "value": 6.45,
        "unit": "g"
      },
      "polyunsaturated_fat": {
        "value": 2.1,
        "unit": "g"
      },
      "guarana": {
        "value": 0,
        "unit": "mg"
      },
      "inositol": {
        "value": 0,
        "unit": "g"
      },
      "inulin": {
        "value": 0,
        "unit": "g"
      },
      "iodine": {
        "value": 0,
        "unit": "mg"
      },
      "l_carnitine": {
        "value": 0,
        "unit": "mg"
      },
      "l_methionine": {
        "value": 0,
        "unit": "g"
      },
      "lactose": {
        "value": 0,
        "unit": "g"
      },
      "magnesium": {
        "value": 22.03499999999995,
        "unit": "mg"
      },
      "maltose": {
        "value": 0,
        "unit": "g"
      },
      "manganese": {
        "value": 0.2609999999999995,
        "unit": "mg"
      },
      "molybdenum": {
        "value": 0,
        "unit": "mcg"
      },
      "linolenic_acid": {
        "value": 0.12,
        "unit": "g"
      },
      "linoleic_acid": {
        "value": 1.935,
        "unit": "g"
      },
      "omega_7": {
        "value": 0,
        "unit": "mg"
      },
      "omega_9": {
        "value": 0,
        "unit": "mg"
      },
      "oleic_acid": {
        "value": 6.18,
        "unit": "g"
      },
      "other_carbo": {
        "value": 0,
        "unit": "g"
      },
      "polydextrose": {
        "value": 0,
        "unit": "g"
      },
      "polyols": {
        "value": 0,
        "unit": "g"
      },
      "potassium": {
        "value": 309.4648000000005,
        "unit": "mg"
      },
      "sacarose": {
        "value": 0,
        "unit": "g"
      },
      "selenium": {
        "value": 0.001,
        "unit": "mcg"
      },
      "silicon": {
        "value": 0,
        "unit": "mg"
      },
      "sorbitol": {
        "value": 0,
        "unit": "g"
      },
      "sucralose": {
        "value": 0,
        "unit": "g"
      },
      "taurine": {
        "value": 0,
        "unit": "mg"
      },
      "vitamin_a": {
        "value": 0,
        "unit": "IU"
      },
      "vitamin_b1": {
        "value": 0,
        "unit": "mg"
      },
      "vitamin_b2": {
        "value": 0,
        "unit": "mg"
      },
      "vitamin_b3": {
        "value": 0,
        "unit": "mg"
      },
      "vitamin_b5": {
        "value": 0,
        "unit": "mg"
      },
      "vitamin_b6": {
        "value": 0,
        "unit": "mg"
      },
      "folic_acid": {
        "value": 0,
        "unit": "mcg"
      },
      "vitamin_b12": {
        "value": 0,
        "unit": "mcg"
      },
      "vitamin_c": {
        "value": 12.99,
        "unit": "mg"
      },
      "vitamin_d": {
        "value": 0,
        "unit": "IU"
      },
      "vitamin_e": {
        "value": 0,
        "unit": "mg"
      },
      "vitamin_k": {
        "value": 0,
        "unit": "mcg"
      },
      "zinc": {
        "value": 0.3260000000000005,
        "unit": "mg"
      },
      "retinol": {
        "value": 0,
        "unit": "mcg"
      },
      "thiamine": {
        "value": 0,
        "unit": "mg"
      },
      "riboflavin": {
        "value": 0.0649999999999995,
        "unit": "mg"
      },
      "pyridoxine": {
        "value": 0,
        "unit": "mg"
      },
      "niacin": {
        "value": 0,
        "unit": "mg"
      }
    },
    "weight_in_grams": None,
    "image_url": None,
    "created_at": "2025-09-16T19:16:25.227457Z",
    "updated_at": "2025-09-16T20:59:07.124193Z",
    "average_taste_rating": None,
    "average_convenience_rating": None
  }