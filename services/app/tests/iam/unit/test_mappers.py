import pytest
from src.contexts.iam.shared.adapters.ORM.mappers.user import UserMapper
from src.contexts.iam.shared.adapters.ORM.sa_models.role import RoleSaModel
from src.contexts.iam.shared.adapters.ORM.sa_models.user import UserSaModel
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.domain.enums import Role as EnumRoles
from src.contexts.iam.shared.domain.value_objects.role import Role


@pytest.fixture
def sa_model_user() -> UserSaModel:
    return UserSaModel(
        id="1",
        roles=[
            RoleSaModel(
                name=EnumRoles.ADMINISTRATOR.name.lower(),
                context="IAM",
                permissions=", ".join([i.value for i in EnumRoles.ADMINISTRATOR.value]),
            )
        ],
        discarded=False,
        version="1",
    )


@pytest.fixture
def domain_model_user() -> User:
    return User(
        id="1",
        roles=[Role.administrator()],
        discarded=False,
        version="1",
    )


def test_map_domain_to_sa_model(
    domain_model_user: User,
) -> None:
    mapper = UserMapper()
    sa_model = mapper.map_domain_to_sa(domain_model_user)
    assert sa_model.id == "1"
    assert sa_model.roles[0].name == EnumRoles.ADMINISTRATOR.name.lower()
    assert sa_model.roles[0].context == "IAM"
    assert all(
        [
            i in [j.value for j in list(EnumRoles.ADMINISTRATOR.value)]
            for i in sa_model.roles[0].permissions.split(", ")
        ]
    )
    assert sa_model.discarded is False
    assert sa_model.version == "1"


def test_map_sa_to_domain_model(sa_model_user: UserSaModel) -> None:
    mapper = UserMapper()
    domain_model = mapper.map_sa_to_domain(sa_model_user)
    assert domain_model.id == "1"
    assert domain_model.roles[0].name == EnumRoles.ADMINISTRATOR.name.lower()
    assert domain_model.roles[0].context == "IAM"
    assert all(
        [
            i in [j.value for j in list(EnumRoles.ADMINISTRATOR.value)]
            for i in domain_model.roles[0].permissions
        ]
    )
    assert domain_model.discarded is False
    assert domain_model.version == "1"
