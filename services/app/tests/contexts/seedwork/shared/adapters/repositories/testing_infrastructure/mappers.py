"""
Data mappers between domain entities and SQLAlchemy models

This module contains all the mapping logic between domain entities and 
SQLAlchemy models for the test infrastructure. These mappers handle the
translation between the domain layer (business logic) and the persistence
layer (database models).

Key responsibilities:
- Convert domain entities to SQLAlchemy models for persistence
- Convert SQLAlchemy models back to domain entities for business logic
- Handle complex attribute mapping and default values
- Maintain data integrity during conversions

Following the Repository pattern, these mappers isolate domain entities
from database concerns, allowing business logic to remain pure.
"""

from datetime import datetime, timezone

from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper

from .models import (
    MealSaTestModel, RecipeSaTestModel, CircularTestModelA, CircularTestModelB,
    SelfReferentialTestModel, TagSaTestModel, RatingSaTestModel, IngredientSaTestModel
)
from .entities import (
    TestMealEntity, TestRecipeEntity, TestCircularEntityA, TestCircularEntityB,
    TestSelfReferentialEntity, TestTagEntity, TestRatingEntity, TestIngredientEntity
)


class TestMealMapper(ModelMapper):
    """
    Real mapper for test meal model
    
    Handles bidirectional mapping between TestMealEntity (domain) and 
    TestMealSaModel (SQLAlchemy). Ensures all business attributes are
    properly persisted and retrieved.
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestMealEntity) -> MealSaTestModel:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return MealSaTestModel(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=getattr(domain_obj, 'author_id', 'test_author'),
            preprocessed_name=getattr(domain_obj, 'preprocessed_name', domain_obj.name.lower()),
            description=getattr(domain_obj, 'description', None),
            menu_id=getattr(domain_obj, 'menu_id', None),
            notes=getattr(domain_obj, 'notes', None),
            total_time=getattr(domain_obj, 'total_time', None),
            like=getattr(domain_obj, 'like', None),
            weight_in_grams=getattr(domain_obj, 'weight_in_grams', None),
            calorie_density=getattr(domain_obj, 'calorie_density', None),
            carbo_percentage=getattr(domain_obj, 'carbo_percentage', None),
            protein_percentage=getattr(domain_obj, 'protein_percentage', None),
            total_fat_percentage=getattr(domain_obj, 'total_fat_percentage', None),
            image_url=getattr(domain_obj, 'image_url', None),
            created_at=getattr(domain_obj, 'created_at', datetime.now(timezone.utc).replace(tzinfo=None)),
            updated_at=getattr(domain_obj, 'updated_at', datetime.now(timezone.utc).replace(tzinfo=None)),
            discarded=getattr(domain_obj, 'discarded', False),
            version=getattr(domain_obj, 'version', 1),
            # Individual nutritional components for composite nutri_facts
            calories=getattr(domain_obj, 'calories', None),
            protein=getattr(domain_obj, 'protein', None),
            carbohydrate=getattr(domain_obj, 'carbohydrate', None),
            total_fat=getattr(domain_obj, 'total_fat', None),
            saturated_fat=getattr(domain_obj, 'saturated_fat', None),
            trans_fat=getattr(domain_obj, 'trans_fat', None),
            dietary_fiber=getattr(domain_obj, 'dietary_fiber', None),
            sodium=getattr(domain_obj, 'sodium', None),
            sugar=getattr(domain_obj, 'sugar', None),
            vitamin_a=getattr(domain_obj, 'vitamin_a', None),
            vitamin_c=getattr(domain_obj, 'vitamin_c', None),
            iron=getattr(domain_obj, 'iron', None),
            calcium=getattr(domain_obj, 'calcium', None),
        )
    
    @staticmethod
    def map_sa_to_domain(sa_obj: MealSaTestModel) -> TestMealEntity:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestMealEntity(
            id=sa_obj.id, 
            name=sa_obj.name,
            author_id=sa_obj.author_id,
            preprocessed_name=sa_obj.preprocessed_name,
            description=sa_obj.description,
            menu_id=sa_obj.menu_id,
            notes=sa_obj.notes,
            total_time=sa_obj.total_time,
            like=sa_obj.like,
            weight_in_grams=sa_obj.weight_in_grams,
            calorie_density=sa_obj.calorie_density,
            carbo_percentage=sa_obj.carbo_percentage,
            protein_percentage=sa_obj.protein_percentage,
            total_fat_percentage=sa_obj.total_fat_percentage,
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
            # Individual nutritional components from composite nutri_facts
            calories=sa_obj.calories,
            protein=sa_obj.protein,
            carbohydrate=sa_obj.carbohydrate,
            total_fat=sa_obj.total_fat,
            saturated_fat=sa_obj.saturated_fat,
            trans_fat=sa_obj.trans_fat,
            dietary_fiber=sa_obj.dietary_fiber,
            sodium=sa_obj.sodium,
            sugar=sa_obj.sugar,
            vitamin_a=sa_obj.vitamin_a,
            vitamin_c=sa_obj.vitamin_c,
            iron=sa_obj.iron,
            calcium=sa_obj.calcium,
        )


class TestRecipeMapper(ModelMapper):
    """
    Real mapper for test recipe model
    
    Handles complex recipe entity mapping including relationships to
    meals, ingredients, ratings, and nutritional information.
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestRecipeEntity) -> RecipeSaTestModel:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return RecipeSaTestModel(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=getattr(domain_obj, 'author_id', 'test_author'),
            preprocessed_name=getattr(domain_obj, 'preprocessed_name', domain_obj.name.lower()),
            description=getattr(domain_obj, 'description', None),
            instructions=getattr(domain_obj, 'instructions', 'Test instructions'),
            meal_id=getattr(domain_obj, 'meal_id', None),
            utensils=getattr(domain_obj, 'utensils', None),
            total_time=getattr(domain_obj, 'total_time', None),
            notes=getattr(domain_obj, 'notes', None),
            privacy=getattr(domain_obj, 'privacy', None),
            weight_in_grams=getattr(domain_obj, 'weight_in_grams', None),
            calorie_density=getattr(domain_obj, 'calorie_density', None),
            carbo_percentage=getattr(domain_obj, 'carbo_percentage', None),
            protein_percentage=getattr(domain_obj, 'protein_percentage', None),
            total_fat_percentage=getattr(domain_obj, 'total_fat_percentage', None),
            image_url=getattr(domain_obj, 'image_url', None),
            created_at=getattr(domain_obj, 'created_at', datetime.now(timezone.utc).replace(tzinfo=None)),
            updated_at=getattr(domain_obj, 'updated_at', datetime.now(timezone.utc).replace(tzinfo=None)),
            discarded=getattr(domain_obj, 'discarded', False),
            version=getattr(domain_obj, 'version', 1),
            average_taste_rating=getattr(domain_obj, 'average_taste_rating', None),
            average_convenience_rating=getattr(domain_obj, 'average_convenience_rating', None),
        )
    
    @staticmethod
    def map_sa_to_domain(sa_obj: RecipeSaTestModel) -> TestRecipeEntity:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestRecipeEntity(
            id=sa_obj.id, 
            name=sa_obj.name,
            author_id=sa_obj.author_id,
            preprocessed_name=sa_obj.preprocessed_name,
            description=sa_obj.description,
            instructions=sa_obj.instructions,
            meal_id=sa_obj.meal_id,
            utensils=sa_obj.utensils,
            total_time=sa_obj.total_time,
            notes=sa_obj.notes,
            privacy=sa_obj.privacy,
            weight_in_grams=sa_obj.weight_in_grams,
            calorie_density=sa_obj.calorie_density,
            carbo_percentage=sa_obj.carbo_percentage,
            protein_percentage=sa_obj.protein_percentage,
            total_fat_percentage=sa_obj.total_fat_percentage,
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
            average_taste_rating=sa_obj.average_taste_rating,
            average_convenience_rating=sa_obj.average_convenience_rating,
        )


class TestCircularMapperA(ModelMapper):
    """
    Mapper for circular model A
    
    Handles mapping for entities involved in circular relationships.
    Keeps mapping simple to focus on relationship testing rather than
    complex attribute handling.
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestCircularEntityA) -> CircularTestModelA:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return CircularTestModelA(
            id=domain_obj.id, 
            name=domain_obj.name,
            b_ref_id=getattr(domain_obj, 'b_ref_id', None)
        )
    
    @staticmethod 
    def map_sa_to_domain(sa_obj: CircularTestModelA) -> TestCircularEntityA:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestCircularEntityA(
            id=sa_obj.id, 
            name=sa_obj.name,
            b_ref_id=sa_obj.b_ref_id
        )


class TestCircularMapperB(ModelMapper):
    """
    Mapper for circular model B
    
    Complements TestCircularMapperA to handle the other side of
    circular relationships.
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestCircularEntityB) -> CircularTestModelB:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return CircularTestModelB(
            id=domain_obj.id, 
            name=domain_obj.name
        )
    
    @staticmethod 
    def map_sa_to_domain(sa_obj: CircularTestModelB) -> TestCircularEntityB:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestCircularEntityB(
            id=sa_obj.id, 
            name=sa_obj.name
        )


class TestSelfReferentialMapper(ModelMapper):
    """
    Mapper for self-referential model
    
    Handles entities that reference themselves, including hierarchical
    relationships (parent-child) and many-to-many self-relationships (friends).
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestSelfReferentialEntity) -> SelfReferentialTestModel:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return SelfReferentialTestModel(
            id=domain_obj.id, 
            name=domain_obj.name,
            parent_id=getattr(domain_obj, 'parent_id', None),
            level=getattr(domain_obj, 'level', 0)
        )
    
    @staticmethod 
    def map_sa_to_domain(sa_obj: SelfReferentialTestModel) -> TestSelfReferentialEntity:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestSelfReferentialEntity(
            id=sa_obj.id, 
            name=sa_obj.name,
            parent_id=sa_obj.parent_id,
            level=sa_obj.level
        )


class TestTagMapper(ModelMapper):
    """
    Mapper for tag model
    
    Handles many-to-many relationship entities with unique constraints.
    Tags can be associated with multiple meals and recipes.
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestTagEntity) -> TagSaTestModel:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return TagSaTestModel(
            id=int(domain_obj.id),  # Convert string ID back to integer for database
            key=domain_obj.key,
            value=domain_obj.value,
            author_id=domain_obj.author_id,
            type=domain_obj.type
        )
    
    @staticmethod 
    def map_sa_to_domain(sa_obj: TagSaTestModel) -> TestTagEntity:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestTagEntity(
            id=sa_obj.id,
            key=sa_obj.key,
            value=sa_obj.value,
            author_id=sa_obj.author_id,
            type=sa_obj.type
        )


class TestRatingMapper(ModelMapper):
    """
    Mapper for rating model
    
    Handles user rating entities with constraint validation and
    foreign key relationships to recipes.
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestRatingEntity) -> RatingSaTestModel:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return RatingSaTestModel(
            id=int(domain_obj.id),  # Convert string ID back to integer for database
            user_id=domain_obj.user_id,
            recipe_id=domain_obj.recipe_id,
            taste=domain_obj.taste,
            convenience=domain_obj.convenience,
            comment=getattr(domain_obj, 'comment', None),
            created_at=getattr(domain_obj, 'created_at', datetime.now(timezone.utc).replace(tzinfo=None))
        )
    
    @staticmethod 
    def map_sa_to_domain(sa_obj: RatingSaTestModel) -> TestRatingEntity:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestRatingEntity(
            id=sa_obj.id,
            user_id=sa_obj.user_id,
            recipe_id=sa_obj.recipe_id,
            taste=sa_obj.taste,
            convenience=sa_obj.convenience,
            comment=sa_obj.comment,
            created_at=sa_obj.created_at
        )


class TestIngredientMapper(ModelMapper):
    """
    Mapper for ingredient model
    
    Handles recipe ingredient entities with ordering (position-based)
    and optional product references.
    """
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj: TestIngredientEntity) -> IngredientSaTestModel:
        """Convert domain entity to SQLAlchemy model for persistence"""
        return IngredientSaTestModel(
            id=int(domain_obj.id),  # Convert string ID back to integer for database
            name=domain_obj.name,
            quantity=domain_obj.quantity,
            unit=domain_obj.unit,
            recipe_id=domain_obj.recipe_id,
            position=getattr(domain_obj, 'position', 0),
            product_id=getattr(domain_obj, 'product_id', None)
        )
    
    @staticmethod 
    def map_sa_to_domain(sa_obj: IngredientSaTestModel) -> TestIngredientEntity:
        """Convert SQLAlchemy model to domain entity for business logic"""
        return TestIngredientEntity(
            id=sa_obj.id,
            name=sa_obj.name,
            quantity=sa_obj.quantity,
            unit=sa_obj.unit,
            recipe_id=sa_obj.recipe_id,
            position=sa_obj.position,
            product_id=sa_obj.product_id
        )