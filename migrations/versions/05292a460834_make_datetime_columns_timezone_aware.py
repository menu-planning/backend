"""make_datetime_columns_timezone_aware

Revision ID: 05292a460834
Revises: 400c5c7a9839
Create Date: 2025-09-10 11:25:41.733262

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "05292a460834"
down_revision = "400c5c7a9839"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert datetime columns to timezone-aware timestamps."""

    # List of tables and their datetime columns that need to be converted
    # Format: (schema, table, column)
    datetime_columns = [
        # Recipes catalog schema
        ("recipes_catalog", "meals", "created_at"),
        ("recipes_catalog", "meals", "updated_at"),
        ("recipes_catalog", "recipes", "created_at"),
        ("recipes_catalog", "recipes", "updated_at"),
        ("recipes_catalog", "menus", "created_at"),
        ("recipes_catalog", "menus", "updated_at"),
        ("recipes_catalog", "ingredients", "created_at"),
        ("recipes_catalog", "ratings", "created_at"),
        ("recipes_catalog", "clients", "created_at"),
        ("recipes_catalog", "clients", "updated_at"),
        # Products catalog schema
        ("products_catalog", "brands", "created_at"),
        ("products_catalog", "brands", "updated_at"),
        ("products_catalog", "sources", "created_at"),
        ("products_catalog", "sources", "updated_at"),
        ("products_catalog", "classifications", "created_at"),
        ("products_catalog", "classifications", "updated_at"),
        ("products_catalog", "products", "created_at"),
        ("products_catalog", "products", "updated_at"),
        # Shared kernel schema
        ("shared_kernel", "tags", "created_at"),
        ("shared_kernel", "tags", "updated_at"),
        ("shared_kernel", "nutri_facts", "created_at"),
        ("shared_kernel", "nutri_facts", "updated_at"),
        # IAM schema
        ("iam", "users", "created_at"),
        ("iam", "users", "updated_at"),
        # Client onboarding schema
        ("client_onboarding", "onboarding_forms", "created_at"),
        ("client_onboarding", "onboarding_forms", "updated_at"),
        ("client_onboarding", "form_responses", "submitted_at"),
        ("client_onboarding", "form_responses", "processed_at"),
        ("client_onboarding", "form_responses", "created_at"),
        ("client_onboarding", "form_responses", "updated_at"),
    ]

    for schema, table, column in datetime_columns:
        # Check if the table and column exist before trying to convert
        connection = op.get_bind()

        # Check if table exists
        table_exists = connection.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = :schema AND table_name = :table
                )
            """
            ),
            {"schema": schema, "table": table},
        ).scalar()

        if not table_exists:
            print(f"Skipping {schema}.{table} - table does not exist")
            continue

        # Check if column exists
        column_exists = connection.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = :schema 
                    AND table_name = :table 
                    AND column_name = :column
                )
            """
            ),
            {"schema": schema, "table": table, "column": column},
        ).scalar()

        if not column_exists:
            print(f"Skipping {schema}.{table}.{column} - column does not exist")
            continue

        # Check current column type
        current_type = connection.execute(
            sa.text(
                """
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = :schema 
                AND table_name = :table 
                AND column_name = :column
            """
            ),
            {"schema": schema, "table": table, "column": column},
        ).scalar()

        if current_type == "timestamp with time zone":
            print(f"Skipping {schema}.{table}.{column} - already timezone aware")
            continue

        print(f"Converting {schema}.{table}.{column} to timezone aware")

        # Convert the column to timezone-aware timestamp using PostgreSQL TIMESTAMP type
        # PostgreSQL will treat existing timestamps as UTC when converting
        op.execute(
            f"""
            ALTER TABLE "{schema}"."{table}" 
            ALTER COLUMN "{column}" 
            TYPE TIMESTAMP WITH TIME ZONE 
            USING "{column}" AT TIME ZONE 'UTC'
        """
        )


def downgrade() -> None:
    """Convert timezone-aware timestamps back to regular timestamps."""

    # Same list of columns to convert back
    datetime_columns = [
        # Recipes catalog schema
        ("recipes_catalog", "meals", "created_at"),
        ("recipes_catalog", "meals", "updated_at"),
        ("recipes_catalog", "recipes", "created_at"),
        ("recipes_catalog", "recipes", "updated_at"),
        ("recipes_catalog", "menus", "created_at"),
        ("recipes_catalog", "menus", "updated_at"),
        ("recipes_catalog", "ingredients", "created_at"),
        ("recipes_catalog", "ratings", "created_at"),
        ("recipes_catalog", "clients", "created_at"),
        ("recipes_catalog", "clients", "updated_at"),
        # Products catalog schema
        ("products_catalog", "brands", "created_at"),
        ("products_catalog", "brands", "updated_at"),
        ("products_catalog", "sources", "created_at"),
        ("products_catalog", "sources", "updated_at"),
        ("products_catalog", "classifications", "created_at"),
        ("products_catalog", "classifications", "updated_at"),
        ("products_catalog", "products", "created_at"),
        ("products_catalog", "products", "updated_at"),
        # Shared kernel schema
        ("shared_kernel", "tags", "created_at"),
        ("shared_kernel", "tags", "updated_at"),
        ("shared_kernel", "nutri_facts", "created_at"),
        ("shared_kernel", "nutri_facts", "updated_at"),
        # IAM schema
        ("iam", "users", "created_at"),
        ("iam", "users", "updated_at"),
        # Client onboarding schema
        ("client_onboarding", "onboarding_forms", "created_at"),
        ("client_onboarding", "onboarding_forms", "updated_at"),
        ("client_onboarding", "form_responses", "submitted_at"),
        ("client_onboarding", "form_responses", "processed_at"),
        ("client_onboarding", "form_responses", "created_at"),
        ("client_onboarding", "form_responses", "updated_at"),
    ]

    for schema, table, column in datetime_columns:
        connection = op.get_bind()

        # Check if table and column exist
        table_exists = connection.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = :schema AND table_name = :table
                )
            """
            ),
            {"schema": schema, "table": table},
        ).scalar()

        if not table_exists:
            continue

        column_exists = connection.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = :schema 
                    AND table_name = :table 
                    AND column_name = :column
                )
            """
            ),
            {"schema": schema, "table": table, "column": column},
        ).scalar()

        if not column_exists:
            continue

        # Check current column type
        current_type = connection.execute(
            sa.text(
                """
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = :schema 
                AND table_name = :table 
                AND column_name = :column
            """
            ),
            {"schema": schema, "table": table, "column": column},
        ).scalar()

        if current_type != "timestamp with time zone":
            continue

        print(f"Converting {schema}.{table}.{column} back to regular timestamp")

        # Convert back to regular timestamp
        op.execute(
            f"""
            ALTER TABLE "{schema}"."{table}" 
            ALTER COLUMN "{column}" 
            TYPE TIMESTAMP WITHOUT TIME ZONE 
            USING "{column}" AT TIME ZONE 'UTC'
        """
        )
