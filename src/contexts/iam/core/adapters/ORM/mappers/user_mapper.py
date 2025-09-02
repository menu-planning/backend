"""Data mappers between IAM domain entities and SQLAlchemy models."""

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.seedwork.adapters.ORM.mappers import helpers
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper


class _RoleMapper(ModelMapper):
    """Mapper for converting between Role value object and RoleSaModel.
    
    Notes:
        Adheres to ModelMapper interface. Performance: avoids N+1 via joinedload.
        Transactions: methods require active UnitOfWork session.
    """
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: Role) -> RoleSaModel:
        """Map domain role to SQLAlchemy role model.
        
        Args:
            session: Database session.
            domain_obj: Domain role object to convert.
        
        Returns:
            Existing SQLAlchemy role model matching the domain role.
        
        Notes:
            Fetches persisted role instead of constructing new instance.
        """
        existing_sa_obj = await helpers.get_sa_entity(
            session=session,
            sa_model_type=RoleSaModel,
            filters={"name": domain_obj.name, "context": domain_obj.context},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: RoleSaModel) -> Role:
        """Map SQLAlchemy role model to domain role.
        
        Args:
            sa_obj: SQLAlchemy role model to convert.
        
        Returns:
            Domain role object.
        """
        return Role(
            sa_obj.name,
            sa_obj.context,
            sa_obj.permissions.split(", "),
        )


class UserMapper(ModelMapper):
    """Mapper for converting between User aggregate and UserSaModel.
    
    Notes:
        Adheres to ModelMapper interface. Eager-loads: roles.
        Performance: avoids N+1 via joinedload on roles.
        Transactions: methods require active UnitOfWork session.
    """
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: User) -> UserSaModel:
        """Map domain user to SQLAlchemy user model.
        
        Args:
            session: Database session.
            domain_obj: Domain user object to convert.
        
        Returns:
            SQLAlchemy user model.
        """
        tasks = (
            [_RoleMapper.map_domain_to_sa(session, i) for i in domain_obj.roles]
            if domain_obj.roles
            else []
        )
        if tasks:
            roles = await helpers.gather_results_with_timeout(
                tasks,
                timeout=5,
                timeout_message="Timeout mapping roles in UserMapper",
            )
        else:
            roles = []
        existing_sa_obj = await helpers.get_sa_entity(
            session=session,
            sa_model_type=UserSaModel,
            filters={"id": domain_obj.id},
        )
        if existing_sa_obj:
            new_sa_obj = UserSaModel(
                id=domain_obj.id,
                roles=roles,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
            await session.merge(new_sa_obj)
            return new_sa_obj
        return UserSaModel(
            id=domain_obj.id,
            roles=roles,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: UserSaModel) -> User:
        """Map SQLAlchemy user model to domain user.
        
        Args:
            sa_obj: SQLAlchemy user model to convert.
        
        Returns:
            Domain user object.
        """
        return User(
            entity_id=sa_obj.id,
            roles=(
                [_RoleMapper.map_sa_to_domain(i) for i in sa_obj.roles]
                if sa_obj.roles
                else []
            ),
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
