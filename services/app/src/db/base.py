import datetime

from sqlalchemy import MetaData, String
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase


class SaBase(DeclarativeBase):
    type_annotation_map = {
        list[str]: ARRAY(String),
        datetime: TIMESTAMP(timezone=True),
    }
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class ViewBase(DeclarativeBase):
    type_annotation_map = {
        list[str]: ARRAY(String),
        datetime: TIMESTAMP(timezone=True),
    }
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


# import src.contexts._receipt_tracker.shared.adapters.ORM.sa_models
# import src.contexts.food_tracker.shared.adapters.ORM.sa_models
# import src.contexts.iam.shared.adapters.ORM.sa_models
# import src.contexts.products_catalog.shared.adapters.ORM.sa_models
# import src.contexts.recipes_catalog.shared.adapters.ORM.sa_models
# import src.contexts.shared_kernel.adapters.ORM.sa_models
