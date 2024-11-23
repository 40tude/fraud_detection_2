import os
import pytest
import random
import datetime
from PIL import Image
from pathlib import Path
from app.user import User
from _pytest.monkeypatch import MonkeyPatch


# -----------------------------------------------------------------------------
# Creates a User object that can be used in multiple tests.
@pytest.fixture
def user() -> User:
    return User(80386, "Zoubida", 42)


# -----------------------------------------------------------------------------
# Check if the `greet` method of the `User` returns the correct greeting message.
def test_user_greet(user: User) -> None:
    assert user.greet() == "Hello, my name is Zoubida and I am 42 years old."


# -----------------------------------------------------------------------------
# `monkeypatch` allows to modify environment variables or objects temporarily.
# We remove the "PASSWORD" environment variable to simulate its absence.
# If `PASSWORD` is not set, we expect a default password to be used.


def test_password_default(monkeypatch: MonkeyPatch) -> None:

    # Remove "PASSWORD" from the environment if it exists.
    monkeypatch.delenv("PASSWORD", raising=False)

    # Define a default password in case "PASSWORD" is not set in the environment.
    default_password = "CPE1704TKS"
    my_password = os.getenv("PASSWORD", default_password)

    # Assert that, since "PASSWORD" is missing, the default password is used.
    assert my_password == default_password


# -----------------------------------------------------------------------------
# Change current working directory to `tmp_path` for the duration of the test.
# This ensures that files created by the test do not affect the actual filesystem.
def test_image_creation(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    # Create an "img" directory and a new PNG image within it.
    img_path = tmp_path / "img"
    img_path.mkdir(parents=True, exist_ok=True)

    # Randomly choose a color for the image background.
    color = random.choice(["blue", "red", "orange", "green"])

    # Create an image with dimensions 100x100 and the chosen background color.
    image = Image.new("RGB", (100, 100), color=color)

    # Generate a filename based on the current timestamp.
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_file = img_path / f"{timestamp}_dummy_artifact.png"

    # Save the image file to `image_file`.
    image.save(image_file)

    # Assert that the image file exists and has the correct properties.
    assert image_file.exists()
    with Image.open(image_file) as img:
        assert img.size == (100, 100)
        assert img.mode == "RGB"
