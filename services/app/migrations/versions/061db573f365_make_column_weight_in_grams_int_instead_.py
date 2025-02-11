"""make column weight_in_grams int instead of float

Revision ID: 061db573f365
Revises: 64b3e6365dab
Create Date: 2025-02-01 16:36:59.691413

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "061db573f365"
down_revision = "64b3e6365dab"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        ALTER TABLE recipes_catalog.recipes 
        ALTER COLUMN weight_in_grams 
        TYPE INTEGER USING ROUND(weight_in_grams);
        """
    )

    op.execute(
        """
        ALTER TABLE recipes_catalog.meals 
        ALTER COLUMN weight_in_grams 
        TYPE INTEGER USING ROUND(weight_in_grams);
        """
    )


def downgrade():
    op.execute(
        """
        ALTER TABLE recipes_catalog.meals 
        ALTER COLUMN weight_in_grams 
        TYPE FLOAT USING weight_in_grams::FLOAT;
        """
    )
    op.execute(
        """
        ALTER TABLE recipes_catalog.recipes 
        ALTER COLUMN weight_in_grams 
        TYPE FLOAT USING weight_in_grams::FLOAT;
        """
    )
