"""Smoke tests to validate CI wiring."""

def test_ci_smoke() -> None:
    """Ensure pytest runs in CI."""
    assert 1 == 1
