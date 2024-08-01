"""delete diet_types from products_catalog

Revision ID: cdd3ea46ba29
Revises: 1db4b711578f
Create Date: 2024-03-16 06:11:34.529742

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cdd3ea46ba29"
down_revision = "1db4b711578f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("products_diet_types_association", schema="products_catalog")
    op.drop_table("diet_types", schema="products_catalog")


def downgrade() -> None:
    op.create_table(
        "products_diet_types_association",
        sa.Column("product_id", sa.String(), nullable=False),
        sa.Column("diet_type_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["diet_type_id"],
            ["products_catalog.diet_types.id"],
            name=op.f("fk_products_diet_types_association_diet_type_id_diet_types"),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products_catalog.products.id"],
            name=op.f("fk_products_diet_types_association_product_id_products"),
        ),
        sa.PrimaryKeyConstraint(
            "product_id",
            "diet_type_id",
            name=op.f("pk_products_diet_types_association"),
        ),
        schema="products_catalog",
    )
    op.create_table(
        "diet_types",
        sa.Column("id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_diet_types")),
        schema="products_catalog",
    )
