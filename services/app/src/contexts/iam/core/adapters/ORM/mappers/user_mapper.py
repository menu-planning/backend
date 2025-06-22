import src.contexts.seedwork.shared.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper


class _RoleMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: Role) -> RoleSaModel:
        """
        Maps a domain object to a SQLAlchemy model object. Since
        the user cannot manipulate any attribute of a role, we
        just need to return the existing SQLAlchemy object.

        """
        existing_sa_obj = await utils.get_sa_entity(
            session=session,
            sa_model_type=RoleSaModel,
            filter={"name": domain_obj.name, "context": domain_obj.context},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: RoleSaModel) -> Role:
        return Role(
            name=sa_obj.name,
            context=sa_obj.context,
            permissions=sa_obj.permissions.split(", "),
        )


class UserMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: User) -> UserSaModel:
        tasks = (
            [_RoleMapper.map_domain_to_sa(session, i) for i in domain_obj.roles]
            if domain_obj.roles
            else []
        )
        if tasks:
            roles = await utils.gather_results_with_timeout(
                tasks,
                timeout=5,
                timeout_message="Timeout mapping roles in UserMapper",
            )
        else:
            roles = []
        existing_sa_obj = await utils.get_sa_entity(
            session=session,
            sa_model_type=UserSaModel,
            filter={"id": domain_obj.id},
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
        return User(
            id=sa_obj.id,
            roles=(
                [_RoleMapper.map_sa_to_domain(i) for i in sa_obj.roles]
                if sa_obj.roles
                else []
            ),
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
