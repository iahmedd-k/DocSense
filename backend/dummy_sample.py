"""Dummy sample code file used to exercise the StorageService upload flow.

This file is intentionally small and self-contained so it can be uploaded to
either Supabase Storage or Cloudinary (whichever is available) as part of the
document upload fallback flow.
"""


def greet(name: str) -> str:
    """Return a friendly greeting."""
    return f"Hello, {name}! Welcome to DocSense."


def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


if __name__ == "__main__":
    print(greet("developer"))
    print(f"2 + 3 = {add(2, 3)}")
