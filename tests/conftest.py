import sys
import os
from unittest.mock import MagicMock, AsyncMock
import pytest
from src.config_manager import ConfigManager
from src.state_manager import StateManager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_config_manager():
    """Provides a mock ConfigManager with pre-configured secret codes."""
    mock = MagicMock(spec=ConfigManager)
    mock.get_all_secret_codes.return_value = {"#s1": "Group_A", "#s2": "Group_B"}
    mock.is_admin.return_value = False
    return mock

@pytest.fixture
def mock_state_manager():
    """Provides a clean mock StateManager."""
    return MagicMock(spec=StateManager)

@pytest.fixture
def mock_line_bot_api():
    """Provides a mock AsyncMessagingApi."""
    api_mock = AsyncMock()
    api_mock.reply_message = AsyncMock()
    return api_mock

@pytest.fixture
def mock_gdrive_service():
    """Provides a clean mock GoogleDriveService for dependency injection."""
    return MagicMock()