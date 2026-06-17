"""Tests for the greet module."""

from parallel_processing.greet import greet


def test_greet() -> None:
    """greet() includes the given name."""
    assert "Alice" in greet("Alice")
