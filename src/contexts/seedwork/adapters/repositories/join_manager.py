from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field
from sqlalchemy import ColumnElement
from src.contexts.seedwork.domain.entity import Entity
from src.db.base import SaBase
from src.logging.logger import get_logger

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.orm import InstrumentedAttribute

@define
class JoinManager[E: Entity, S: SaBase]:
    """Manage table joins for SQLAlchemy query statements.

    This class encapsulates the logic for handling joins to prevent duplicates
    and maintain consistent join tracking across repository operations. It
    ensures that each table is joined only once per query and tracks when
    DISTINCT is needed to prevent duplicate results.

    Type Parameters:
        E: Domain entity type that inherits from Entity
        S: SQLAlchemy model type that inherits from SaBase

    Attributes:
        tracked_joins: Set of already joined table names to prevent duplicates
    """

    tracked_joins: set[str] = field(factory=set)

    def handle_joins(
        self,
        stmt: Select,
        join_specifications: list[tuple[type[SaBase], InstrumentedAttribute | ColumnElement]],
    ) -> tuple[Select, bool]:
        """Handle table joins for the given statement.

        This method processes join specifications and applies them to the
        SQLAlchemy Select statement. It tracks which tables have been joined
        to prevent duplicate joins and determines if DISTINCT is needed.

        Args:
            stmt: The SQLAlchemy Select statement to modify
            join_specifications: List of (join_target, on_clause) tuples

        Returns:
            Tuple of (updated_statement, requires_distinct)
                - updated_statement: The statement with joins applied
                - requires_distinct: True if joins require DISTINCT to prevent duplicates

        Behavior:
            - Applies joins only once per table
            - Sets requires_distinct=True when any join is added
            - Logs join operations for debugging
        """
        if not join_specifications:
            return stmt, False

        requires_distinct = False
        updated_stmt = stmt

        log = get_logger("join_manager")

        for join_target, on_clause in join_specifications:
            join_key = str(join_target)

            if join_key not in self.tracked_joins:
                updated_stmt = updated_stmt.join(join_target, on_clause)
                self.tracked_joins.add(join_key)
                requires_distinct = True

                log.debug(
                    "Join added to query",
                    join_target=join_target.__name__,
                    join_key=join_key,
                    on_clause=str(on_clause),
                    total_joins=len(self.tracked_joins),
                    requires_distinct=requires_distinct
                )
            else:
                log.debug(
                    "Join already tracked, skipping",
                    join_target=join_target.__name__,
                    join_key=join_key,
                    total_joins=len(self.tracked_joins)
                )

        return updated_stmt, requires_distinct

    def add_join(self, join_target: type[SaBase]) -> None:
        """Manually track a join without modifying the statement.

        This method is useful when joins are added outside of the JoinManager
        (e.g., by SQLAlchemy relationships) but still need to be tracked
        to prevent duplicate joins.

        Args:
            join_target: The SQLAlchemy model that was joined
        """
        join_key = str(join_target)
        self.tracked_joins.add(join_key)

        log = get_logger("join_manager")
        log.debug(
            "Join manually tracked",
            join_target=join_target.__name__,
            join_key=join_key,
            total_joins=len(self.tracked_joins)
        )

    def is_join_needed(self, join_target: type[SaBase]) -> bool:
        """Check if a join is needed for the given target.

        Args:
            join_target: The SQLAlchemy model to check

        Returns:
            True if the join hasn't been applied yet, False if already joined
        """
        return str(join_target) not in self.tracked_joins

    def get_tracked_joins(self) -> set[str]:
        """
        Get a copy of the currently tracked joins.

        Returns:
            Set of tracked join keys
        """
        return self.tracked_joins.copy()

    def reset_joins(self) -> None:
        """
        Reset the join tracking state.

        This method clears all tracked joins, allowing the JoinManager
        to be reused for a new query. Useful when building multiple
        queries with the same manager instance.
        """
        self.tracked_joins.clear()

        log = get_logger("join_manager")
        log.debug("Join tracking reset", total_joins=0)

    def merge_tracking(self, other_joins: set[str]) -> None:
        """
        Merge join tracking from another source.

        Args:
            other_joins: Set of join keys to merge into tracking
        """
        if other_joins:
            previous_count = len(self.tracked_joins)
            self.tracked_joins.update(other_joins)

            log = get_logger("join_manager")
            log.debug(
                "Join tracking merged",
                merged_joins=list(other_joins),
                previous_count=previous_count,
                new_total=len(self.tracked_joins),
                added_count=len(other_joins)
            )

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
