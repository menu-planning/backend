from __future__ import annotations

from typing import Annotated, Any, Generic, Type, TypeVar
from attrs import define, field
from sqlalchemy.orm import InstrumentedAttribute

from src.db.base import SaBase
from src.contexts.seedwork.shared.domain.entity import Entity

E = TypeVar("E", bound=Entity)  # , covariant=True)
S = TypeVar("S", bound=SaBase)  # , covariant=True)


@define
class FilterColumnMapper(Generic[E, S]):
    """
    A class used to map filter keys to SQLAlchemy model columns
    and specify join operations in case the filter key is
    associated with a relationship.

    :ivar sa_model_type: The SQLAlchemy model type.
    :vartype sa_model_type: Type[S]
    :ivar mapping: A dictionary mapping filter keys to SQLAlchemy
                   model columns.
    :vartype mapping: Annotated[dict[str, str], "map filter key to
                      sa model column"]
    :ivar join_target_and_on_clause: A list of tuples, where each
                                     tuple contains a target and an
                                     'on' clause for a join operation.
    :vartype join_target_and_on_clause: list[Tuple]

    Example::

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
            Column(
                "diet_type_id", ForeignKey("diet_types.id"), primary_key=True
            ),
        )

        mapper = FilterColumnMapper()
        mapper.sa_model_type = DietType
        mapper.mapping = {'diet_types': 'type'}
        mapper.join_target_and_on_clause=[(DietType, Product.diet_types)],

    In the above example, the `mapper` can be used in the ProductRepo
    to map the `diet_types` filter key to the `type` column of the
    `DietType` model. The `join_target_and_on_clause` attribute is used
    to specify the join operation that should be performed when filtering
    by `diet_types`. In this case, the join operation is between the
    `DietType` model and the `Product.diet_types` relationship.
    """

    sa_model_type: Type[S]
    filter_key_to_column_name: Annotated[
        dict[str, str], "map filter key to sa model column"
    ]
    join_target_and_on_clause: list[tuple[Type[SaBase], InstrumentedAttribute]] | None = field(factory=list)


@define
class Filter:
    """
    This class is used to define a filter for querying data.

    Attributes:
    columns (dict[str, str] | None): A dictionary mapping column names to
      their values. Default is None.
    skip (int | None): The number of records to skip. Default is None.
    limit (int | None): The maximum number of records to return. Default
      is None.
    sort (str | None): The column name to sort by. Default is None.
    others (dict[str, str] | None): A dictionary of other parameters.
      Default is None.
    """

    columns: dict[str, str] | None = None
    skip: int | None = None
    limit: int | None = None
    sort: str | None = None
    others: dict[str, str] | None = None 