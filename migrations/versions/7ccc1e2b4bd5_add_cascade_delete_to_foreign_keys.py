"""add_cascade_delete_to_foreign_keys

Revision ID: 7ccc1e2b4bd5
Revises: 05292a460834
Create Date: 2025-10-07 08:21:04.722884

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ccc1e2b4bd5'
down_revision = '05292a460834'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add ON DELETE CASCADE to foreign key constraints."""
    
    # recipes_catalog.recipes.meal_id -> recipes_catalog.meals.id
    op.drop_constraint(
        'fk_recipes_meal_id_meals',
        'recipes',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_recipes_meal_id_meals',
        'recipes',
        'meals',
        ['meal_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    # recipes_catalog.ingredients.recipe_id -> recipes_catalog.recipes.id
    op.drop_constraint(
        'fk_ingredients_recipe_id_recipes',
        'ingredients',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_ingredients_recipe_id_recipes',
        'ingredients',
        'recipes',
        ['recipe_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    # recipes_catalog.ratings.recipe_id -> recipes_catalog.recipes.id
    op.drop_constraint(
        'fk_ratings_recipe_id_recipes',
        'ratings',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_ratings_recipe_id_recipes',
        'ratings',
        'recipes',
        ['recipe_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    # recipes_catalog.menu_meals.menu_id -> recipes_catalog.menus.id
    op.drop_constraint(
        'fk_menu_items_menu_id_menus',
        'menu_meals',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menu_meals_menu_id_menus',
        'menu_meals',
        'menus',
        ['menu_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    # recipes_catalog.menu_meals.meal_id -> recipes_catalog.meals.id
    op.drop_constraint(
        'fk_menu_items_meal_id_meals',
        'menu_meals',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menu_meals_meal_id_meals',
        'menu_meals',
        'meals',
        ['meal_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    # recipes_catalog.menus.client_id -> recipes_catalog.clients.id
    op.drop_constraint(
        'fk_menus_client_id_clients',
        'menus',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menus_client_id_clients',
        'menus',
        'clients',
        ['client_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    # recipes_catalog.meals.menu_id -> recipes_catalog.menus.id (nullable FK)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_meals_menu_id_menus' 
                AND table_schema = 'recipes_catalog'
                AND table_name = 'meals'
            ) THEN
                ALTER TABLE recipes_catalog.meals 
                DROP CONSTRAINT fk_meals_menu_id_menus;
                
                ALTER TABLE recipes_catalog.meals 
                ADD CONSTRAINT fk_meals_menu_id_menus 
                FOREIGN KEY (menu_id) 
                REFERENCES recipes_catalog.menus(id) 
                ON DELETE SET NULL;
            END IF;
        END $$;
    """)
    
    # Association tables: clients_tags_association
    op.drop_constraint(
        'fk_clients_tags_association_client_id_clients',
        'clients_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_clients_tags_association_client_id_clients',
        'clients_tags_association',
        'clients',
        ['client_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    op.drop_constraint(
        'fk_clients_tags_association_tag_id_tags',
        'clients_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_clients_tags_association_tag_id_tags',
        'clients_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel',
        ondelete='CASCADE'
    )
    
    # Association tables: menus_tags_association
    op.drop_constraint(
        'fk_menus_tags_association_menu_id_menus',
        'menus_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menus_tags_association_menu_id_menus',
        'menus_tags_association',
        'menus',
        ['menu_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    op.drop_constraint(
        'fk_menus_tags_association_tag_id_tags',
        'menus_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menus_tags_association_tag_id_tags',
        'menus_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel',
        ondelete='CASCADE'
    )
    
    # Association tables: meals_tags_association
    op.drop_constraint(
        'fk_meals_tags_association_meal_id_meals',
        'meals_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_meals_tags_association_meal_id_meals',
        'meals_tags_association',
        'meals',
        ['meal_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    op.drop_constraint(
        'fk_meals_tags_association_tag_id_tags',
        'meals_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_meals_tags_association_tag_id_tags',
        'meals_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel',
        ondelete='CASCADE'
    )
    
    # Association tables: recipes_tags_association
    op.drop_constraint(
        'fk_recipes_tags_association_recipe_id_recipes',
        'recipes_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_recipes_tags_association_recipe_id_recipes',
        'recipes_tags_association',
        'recipes',
        ['recipe_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog',
        ondelete='CASCADE'
    )
    
    op.drop_constraint(
        'fk_recipes_tags_association_tag_id_tags',
        'recipes_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_recipes_tags_association_tag_id_tags',
        'recipes_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel',
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove ON DELETE CASCADE from foreign key constraints."""
    
    # Reverse all the CASCADE additions by recreating without ondelete
    
    # recipes_catalog.recipes.meal_id
    op.drop_constraint(
        'fk_recipes_meal_id_meals',
        'recipes',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_recipes_meal_id_meals',
        'recipes',
        'meals',
        ['meal_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    # recipes_catalog.ingredients.recipe_id
    op.drop_constraint(
        'fk_ingredients_recipe_id_recipes',
        'ingredients',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_ingredients_recipe_id_recipes',
        'ingredients',
        'recipes',
        ['recipe_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    # recipes_catalog.ratings.recipe_id
    op.drop_constraint(
        'fk_ratings_recipe_id_recipes',
        'ratings',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_ratings_recipe_id_recipes',
        'ratings',
        'recipes',
        ['recipe_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    # recipes_catalog.menu_meals.menu_id
    op.drop_constraint(
        'fk_menu_meals_menu_id_menus',
        'menu_meals',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menu_items_menu_id_menus',
        'menu_meals',
        'menus',
        ['menu_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    # recipes_catalog.menu_meals.meal_id
    op.drop_constraint(
        'fk_menu_meals_meal_id_meals',
        'menu_meals',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menu_items_meal_id_meals',
        'menu_meals',
        'meals',
        ['meal_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    # recipes_catalog.menus.client_id
    op.drop_constraint(
        'fk_menus_client_id_clients',
        'menus',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menus_client_id_clients',
        'menus',
        'clients',
        ['client_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    # recipes_catalog.meals.menu_id
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_meals_menu_id_menus' 
                AND table_schema = 'recipes_catalog'
                AND table_name = 'meals'
            ) THEN
                ALTER TABLE recipes_catalog.meals 
                DROP CONSTRAINT fk_meals_menu_id_menus;
                
                ALTER TABLE recipes_catalog.meals 
                ADD CONSTRAINT fk_meals_menu_id_menus 
                FOREIGN KEY (menu_id) 
                REFERENCES recipes_catalog.menus(id);
            END IF;
        END $$;
    """)
    
    # Association tables downgrades
    # clients_tags_association
    op.drop_constraint(
        'fk_clients_tags_association_client_id_clients',
        'clients_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_clients_tags_association_client_id_clients',
        'clients_tags_association',
        'clients',
        ['client_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    op.drop_constraint(
        'fk_clients_tags_association_tag_id_tags',
        'clients_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_clients_tags_association_tag_id_tags',
        'clients_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel'
    )
    
    # menus_tags_association
    op.drop_constraint(
        'fk_menus_tags_association_menu_id_menus',
        'menus_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menus_tags_association_menu_id_menus',
        'menus_tags_association',
        'menus',
        ['menu_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    op.drop_constraint(
        'fk_menus_tags_association_tag_id_tags',
        'menus_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_menus_tags_association_tag_id_tags',
        'menus_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel'
    )
    
    # meals_tags_association
    op.drop_constraint(
        'fk_meals_tags_association_meal_id_meals',
        'meals_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_meals_tags_association_meal_id_meals',
        'meals_tags_association',
        'meals',
        ['meal_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    op.drop_constraint(
        'fk_meals_tags_association_tag_id_tags',
        'meals_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_meals_tags_association_tag_id_tags',
        'meals_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel'
    )
    
    # recipes_tags_association
    op.drop_constraint(
        'fk_recipes_tags_association_recipe_id_recipes',
        'recipes_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_recipes_tags_association_recipe_id_recipes',
        'recipes_tags_association',
        'recipes',
        ['recipe_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='recipes_catalog'
    )
    
    op.drop_constraint(
        'fk_recipes_tags_association_tag_id_tags',
        'recipes_tags_association',
        schema='recipes_catalog',
        type_='foreignkey'
    )
    op.create_foreign_key(
        'fk_recipes_tags_association_tag_id_tags',
        'recipes_tags_association',
        'tags',
        ['tag_id'],
        ['id'],
        source_schema='recipes_catalog',
        referent_schema='shared_kernel'
    )
