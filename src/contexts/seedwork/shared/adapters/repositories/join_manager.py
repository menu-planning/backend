from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field
from src.contexts.seedwork.shared.domain.entity import Entity
from src.db.base import SaBase
from src.logging.logger import structlog_logger

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.orm import InstrumentedAttribute

@define
class JoinManager[E: Entity, S: SaBase]:
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

        log = structlog_logger("join_manager")
        
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
        """
        Manually track a join without modifying the statement.

        Args:
            join_target: The SQLAlchemy model that was joined
        """
        join_key = str(join_target)
        self.tracked_joins.add(join_key)
        
        log = structlog_logger("join_manager")
        log.debug(
            "Join manually tracked",
            join_target=join_target.__name__,
            join_key=join_key,
            total_joins=len(self.tracked_joins)
        )

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
        previous_count = len(self.tracked_joins)
        self.tracked_joins.clear()
        
        if previous_count > 0:
            log = structlog_logger("join_manager")
            log.debug(
                "Join tracking reset",
                previous_joins_count=previous_count
            )

    def merge_tracking(self, other_joins: set[str]) -> None:
        """
        Merge join tracking from another source.

        Args:
            other_joins: Set of join keys to merge into tracking
        """
        if other_joins:
            previous_count = len(self.tracked_joins)
            self.tracked_joins.update(other_joins)
            
            log = structlog_logger("join_manager")
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
