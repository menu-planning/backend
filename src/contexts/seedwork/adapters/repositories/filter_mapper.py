from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from attrs import define, field
from src.contexts.seedwork.domain.entity import Entity
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject
from src.db.base import SaBase

if TYPE_CHECKING:
    from sqlalchemy.orm import InstrumentedAttribute

@define
class FilterColumnMapper[D: Entity | ValueObject, S: SaBase]:
    """Map filter keys to SQLAlchemy model columns and join operations.

    This class provides a configuration-driven approach to building dynamic
    database queries. It maps API filter keys to database columns and specifies
    join operations when filters involve related tables.

    Type Parameters:
        E: Domain entity type that inherits from Entity
        S: SQLAlchemy model type that inherits from SaBase

    Attributes:
        sa_model_type: The SQLAlchemy model type for the target table
        filter_key_to_column_name: Dictionary mapping filter keys to column names
        join_target_and_on_clause: List of (target_model, on_clause) tuples for joins

    Example:
        ```python
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        class Product(Base):
            __tablename__ = "products"
            id: Mapped[sa_field.strpk]
            diet_types: Mapped[list[DietType]] = relationship(
                secondary=products_diet_types_association, lazy="selectin"
            )

        class DietType(Base):
            __tablename__ = "diet_types"
            type: Mapped[sa_field.strpk]

        products_diet_types_association = Table(
            "products_diet_types_association",
            Base.metadata,
            Column("product_id", ForeignKey("products.id"), primary_key=True),
            Column("diet_type_id", ForeignKey("diet_types.id"), primary_key=True),
        )

        mapper = FilterColumnMapper()
        mapper.sa_model_type = DietType
        mapper.mapping = {'diet_types': 'type'}
        mapper.join_target_and_on_clause=[(DietType, Product.diet_types)]
        ```

        In the above example, the `mapper` can be used in the ProductRepo
        to map the `diet_types` filter key to the `type` column of the
        `DietType` model. The `join_target_and_on_clause` attribute is used
        to specify the join operation that should be performed when filtering
        by `diet_types`.
    """

    sa_model_type: type[S]
    filter_key_to_column_name: Annotated[
        dict[str, str], "map filter key to sa model column"
    ]
    join_target_and_on_clause: (
        list[tuple[type[SaBase], InstrumentedAttribute]] | None
    ) = field(factory=list)

