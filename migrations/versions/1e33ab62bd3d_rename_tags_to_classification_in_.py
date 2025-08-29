"""Rename tags to classification in products_catalog schema

Revision ID: 1e33ab62bd3d
Revises: fbe187edafef
Create Date: 2024-12-19 08:58:28.602567

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1e33ab62bd3d"
down_revision = "fbe187edafef"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("tags", "classification", schema="products_catalog")


def downgrade():
    op.rename_table("classification", "tags", schema="products_catalog")
