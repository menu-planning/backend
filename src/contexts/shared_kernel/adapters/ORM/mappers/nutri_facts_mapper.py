"""Mappers for converting NutriFacts between domain and SQLAlchemy models.

This module provides utilities to translate the `NutriFacts` value object to and
from its SQLAlchemy composite dataclass representation `NutriFactsSaModel`.
"""

from dataclasses import asdict as dataclass_asdict

from attrs import asdict as attrs_asdict
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class NutriFactsMapper(ModelMapper):
    """Mapper between NutriFacts domain object and NutriFactsSaModel.

    Notes:
        Adheres to ModelMapper interface. Lossless mapping with proper type conversion.
        Performance: Efficient conversion between domain and ORM representations.
        Transactions: methods require active UnitOfWork session.
    """
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: NutriFacts | None,
    ) -> NutriFactsSaModel:
        """Convert a domain object into a SQLAlchemy composite dataclass.

        Args:
            session: Async session reference (kept for interface consistency).
            domain_obj: Domain value object to convert. If None, returns an
                empty `NutriFactsSaModel` instance.

        Returns:
            A `NutriFactsSaModel` instance representing the given domain object.
        """
        return (
            NutriFactsSaModel(
                **{k: v["value"] for k, v in attrs_asdict(domain_obj).items()}
            )
            if domain_obj
            else NutriFactsSaModel()
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: NutriFactsSaModel) -> NutriFacts | None:
        """Convert a SQLAlchemy composite dataclass into a domain object.

        Args:
            sa_obj: The SQLAlchemy composite dataclass to convert.

        Returns:
            A `NutriFacts` instance, or None if all fields in the composite are
            None.
        """
        try:
            nutri_facts = set(dataclass_asdict(sa_obj).values())
            return (
                NutriFacts(**dataclass_asdict(sa_obj))
                if nutri_facts != {None}
                else None
            )
        except Exception:
            return NutriFacts(**dataclass_asdict(sa_obj))
