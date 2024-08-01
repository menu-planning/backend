from src.contexts.iam.shared.adapters.ORM.sa_models.role import RoleSaModel
from src.contexts.iam.shared.adapters.ORM.sa_models.user import UserSaModel
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.domain.value_objects.role import Role
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class _RoleMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Role) -> RoleSaModel:
        return RoleSaModel(
            name=domain_obj.name,
            context=domain_obj.context,
            permissions=", ".join(domain_obj.permissions),
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: RoleSaModel) -> Role:
        return Role(
            name=sa_obj.name,
            context=sa_obj.context,
            permissions=sa_obj.permissions.split(", "),
        )


class UserMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: User) -> UserSaModel:
        return UserSaModel(
            id=domain_obj.id,
            roles=(
                [_RoleMapper.map_domain_to_sa(i) for i in domain_obj.roles]
                if domain_obj.roles
                else []
            ),
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
