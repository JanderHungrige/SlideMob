"""Contains a test for version availability using non-relative imports."""

from slidemob import __version__


def test_package_version_exists():
    """The version tag should exist."""
    assert __version__
