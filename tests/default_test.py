"""Module for default tests."""

from recipes.main import main


def test_default() -> None:
    """Default test: will always pass."""
    assert True


def test_main() -> None:
    """Test import of the main function."""
    assert main() is True
