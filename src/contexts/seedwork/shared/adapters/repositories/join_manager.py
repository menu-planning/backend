from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from attrs import define, field

from src.contexts.seedwork.shared.domain.entity import Entity
from src.db.base import SaBase
from src.logging.logger import logger

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.orm import InstrumentedAttribute

E = TypeVar("E", bound=Entity)
S = TypeVar("S", bound=SaBase)


@define
class JoinManager(Generic[E, S]):
    """
    Manages table joins for SQLAlchemy query statements.

    This class encapsulates the logic for handling joins to prevent duplicates
    and maintain consistent join tracking across repository operations.

    Attributes:
        tracked_joins: A set of already joined table names to prevent duplicates
    """

    tracked_joins: set[str] = field(factory=set)

    def handle_joins(
        self,
        stmt: Select,
        join_specifications: list[tuple[type[SaBase], InstrumentedAttribute]],
    ) -> tuple[Select, bool]:
        """
        Handle table joins for the given statement.

        Args:
            stmt: The SQLAlchemy Select statement
            join_specifications: List of (join_target, on_clause) tuples

        Returns:
            Tuple of (updated_statement, requires_distinct)
            - updated_statement: The statement with joins applied
            - requires_distinct: True if joins require DISTINCT to prevent duplicates
        """
        if not join_specifications:
            return stmt, False

        requires_distinct = False
        updated_stmt = stmt

        for join_target, on_clause in join_specifications:
            join_key = str(join_target)

            if join_key not in self.tracked_joins:
                logger.debug(f"Adding join: {join_target} on {on_clause}")
                updated_stmt = updated_stmt.join(join_target, on_clause)
                self.tracked_joins.add(join_key)
                requires_distinct = True
            else:
                logger.debug(f"Join already exists for {join_target}, skipping")

        return updated_stmt, requires_distinct

    def add_join(self, join_target: type[SaBase]) -> None:
        """
        Manually track a join without modifying the statement.

        Args:
            join_target: The SQLAlchemy model that was joined
        """
        join_key = str(join_target)
        self.tracked_joins.add(join_key)
        logger.debug(f"Manually tracking join: {join_key}")

    def is_join_needed(self, join_target: type[SaBase]) -> bool:
        """
        Check if a join is needed for the given target.

        Args:
            join_target: The SQLAlchemy model to check

        Returns:
            True if join is needed, False if already joined
        """
        join_key = str(join_target)
        return join_key not in self.tracked_joins

    def get_tracked_joins(self) -> set[str]:
        """
        Get a copy of the currently tracked joins.

        Returns:
            Set of tracked join keys
        """
        return self.tracked_joins.copy()

    def reset(self) -> None:
        """
        Reset the join tracking state.

        This should be called when starting a new query to ensure
        fresh join tracking.
        """
        self.tracked_joins.clear()
        logger.debug("Join tracking reset")

    def merge_tracking(self, other_joins: set[str]) -> None:
        """
        Merge join tracking from another source.

        Args:
            other_joins: Set of join keys to merge into tracking
        """
        self.tracked_joins.update(other_joins)
        logger.debug(f"Merged join tracking: {other_joins}")

    @classmethod
    def create_with_existing_joins(cls, existing_joins: set[str]) -> JoinManager[E, S]:
        """
        Create a JoinManager with pre-existing join tracking.

        Args:
            existing_joins: Set of already joined table names

        Returns:
            JoinManager instance with pre-populated join tracking
        """
        manager = cls()
        manager.tracked_joins = existing_joins.copy()
        return manager
