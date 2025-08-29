"""delete meals diet types and meals season associations

Revision ID: 8bbd0d2e6d93
Revises: 66a376c8f145
Create Date: 2025-01-23 09:57:52.465951

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8bbd0d2e6d93"
down_revision = "66a376c8f145"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("meals_diet_types_association", schema="recipes_catalog")
    op.drop_table("meals_season_association", schema="recipes_catalog")


def downgrade() -> None:
    pass
