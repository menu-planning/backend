"""make index tags_author_id_type not unique

Revision ID: 64b3e6365dab
Revises: 082ec09c42ff
Create Date: 2025-01-26 12:15:13.613226

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "64b3e6365dab"
down_revision = "082ec09c42ff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "tags_author_id_type,unique", table_name="tags", schema="shared_kernel"
    )
    op.create_index(
        "tags_author_id_type",
        "tags",
        ["author_id", "type"],
        unique=False,
        schema="shared_kernel",
    )


def downgrade() -> None:
    pass
