"""Fixtures de pytest para el scanner worker."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_session() -> MagicMock:
    """Mock de SQLAlchemy Session."""
    return MagicMock()

