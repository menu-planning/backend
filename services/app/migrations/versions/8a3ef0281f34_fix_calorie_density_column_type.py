"""fix calorie_density column type

Revision ID: 8a3ef0281f34
Revises: b68587e33b73
Create Date: 2024-06-16 20:59:59.476572

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8a3ef0281f34"
down_revision = "b68587e33b73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE recipes_catalog.recipes 
        ALTER COLUMN calorie_density 
        TYPE FLOAT USING 
        CASE WHEN calorie_density THEN 1.0 ELSE 0.0 END
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE recipes_catalog.recipes 
        ALTER COLUMN calorie_density 
        TYPE BOOLEAN USING 
        CASE WHEN calorie_density = 1.0 THEN TRUE ELSE FALSE END
        """
    )
