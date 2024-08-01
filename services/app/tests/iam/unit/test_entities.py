import pytest
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.domain.events import UserCreated
from src.contexts.shared_kernel.domain.exceptions import DiscardedEntityException


@pytest.fixture
def user() -> User:
    return User(
        id="test_id",
    )


def test_create_user(user: User):
    assert user.id == "test_id"


def test_cannot_manipulate_discarded_user(user: User):
    user.delete()
    with pytest.raises(DiscardedEntityException):
        user.id


def test_create_user_creates_UserCreated_event():
    user = User.create_user(
        id="test_id",
    )
    event = UserCreated(
        user_id=user.id,
    )
    assert user.events[0] == event


def test_increment_version(user: User):
    initial_version = user.version
    user._increment_version()
    assert user.version == initial_version + 1


def test_cannot_update_properties(user: User):
    assert user._update_properties() == NotImplemented
