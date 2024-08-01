from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Table
from src.db.base import SaBase

user_role_association = Table(
    "user_role_association",
    SaBase.metadata,
    Column("user_id", ForeignKey("iam.users.id"), primary_key=True),
    Column("role_name", primary_key=True),
    Column("role_context", primary_key=True),
    # This composite foreign key references the composite primary key of the RoleSaModel
    ForeignKeyConstraint(
        ["role_name", "role_context"], ["iam.roles.name", "iam.roles.context"]
    ),
    schema="iam",
)
