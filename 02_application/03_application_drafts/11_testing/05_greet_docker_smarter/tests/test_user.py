import pytest

from app.user import User


# ! FIXTURE
# returns a new User instance with an ID, name and age.
# We then passed this fixture as an argument to our test functions, allowing us to reuse the User instance across multiple tests
#       - test_user_creation() : to test that the User object is created with the correct name and age
#       - test_greet()         : to test the greet method’s output.
@pytest.fixture
def user() -> User:
    """Pytest fixture to create a User instance for testing."""
    return User(1, "John Doe", 30)


def test_user_creation(user: User) -> None:
    """Test the creation of a User instance."""
    assert user.id == 1
    assert user.name == "John Doe"
    assert user.age == 30


def test_greet(user: User) -> None:
    """Test the greet method of a User instance."""
    greeting: str = user.greet()
    assert greeting == "Hello, my name is John Doe and I am 30 years old."
