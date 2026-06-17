"""A tiny sample module to check the environment."""

import sys


def greet(name: str) -> str:
    """Return a greeting message."""
    major = sys.version_info.major
    minor = sys.version_info.minor
    return f"Hello, {name}! Running on Python {major}.{minor}"


if __name__ == "__main__":
    print(greet("Nix + uv"))
