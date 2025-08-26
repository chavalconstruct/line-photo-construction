import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.webhook_processor import process_webhook_event
from src.state_manager import StateManager
from src.config_manager import ConfigManager
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    UserSource,
    DeliveryContext,
    ContentProvider, # <-- IMPORT THIS
)

# A complete, reusable MessageEvent creator
def create_mock_event(user_id, message_content):
    """Helper function to create a valid MessageEvent object for tests."""
    return MessageEvent(
        source=UserSource(user_id=user_id),
        message=message_content,
        timestamp=1673377200000,
        mode="active",
        webhook_event_id="01GA0000000000000000000000000000",
        delivery_context=DeliveryContext(is_redelivery=False)
    )

@pytest.fixture
def mock_config_manager():
    mock = MagicMock(spec=ConfigManager)
    mock.get_group_from_secret_code.return_value = "Group_A"
    mock.get_app_user.return_value = "Alice"
    return mock

@pytest.fixture
def mock_state_manager():
    return MagicMock(spec=StateManager)

@pytest.fixture
def mock_line_bot_api():
    return AsyncMock()

@pytest.mark.asyncio
async def test_handles_secret_code_and_sets_state(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 1: Handles a secret code and sets the user's state."""
    text_message = TextMessageContent(id="123", text="#s1", quote_token="dummy_token")
    event = create_mock_event("U12345", text_message)

    await process_webhook_event(
        event=event,
        state_manager=mock_state_manager,
        config_manager=mock_config_manager,
        line_bot_api=mock_line_bot_api,
        channel_access_token="dummy_token",
        parent_folder_id="dummy_parent_id"
    )

    mock_config_manager.get_group_from_secret_code.assert_called_once_with("#s1")
    mock_state_manager.set_pending_upload.assert_called_once_with("U12345", "Group_A")

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_handles_image_when_user_is_pending(
    mock_download, mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 2: Handles an image for a user in a pending state."""
    mock_download.return_value = b'fake-image-bytes'
    mock_gdrive_instance = mock_gdrive_service_class.return_value
    mock_gdrive_instance.find_or_create_folder.return_value = "folder_123"
    mock_gdrive_instance.upload_file.return_value = "file_456"
    mock_state_manager.consume_pending_upload.return_value = "Group_A"

    # FIX IS HERE: Added content_provider
    image_message = ImageMessageContent(
        id="msg_abc",
        quote_token="dummy_token",
        content_provider=ContentProvider(type="line")
    )
    event = create_mock_event("U12345", image_message)

    await process_webhook_event(
        event=event,
        state_manager=mock_state_manager,
        config_manager=mock_config_manager,
        line_bot_api=mock_line_bot_api,
        channel_access_token="dummy_token",
        parent_folder_id="dummy_parent_id"
    )

    mock_state_manager.consume_pending_upload.assert_called_once_with("U12345")
    mock_download.assert_called_once()
    mock_gdrive_instance.find_or_create_folder.assert_called_once_with("Group_A", parent_folder_id="dummy_parent_id")
    mock_gdrive_instance.upload_file.assert_called_once()

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_ignores_image_when_user_is_not_pending(
    mock_download, mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 3: Ignores an image if the user is not in a pending state."""
    mock_state_manager.consume_pending_upload.return_value = None
    mock_gdrive_instance = mock_gdrive_service_class.return_value

    # FIX IS HERE: Added content_provider
    image_message = ImageMessageContent(
        id="msg_abc",
        quote_token="dummy_token",
        content_provider=ContentProvider(type="line")
    )
    event = create_mock_event("U12345", image_message)

    await process_webhook_event(
        event=event,
        state_manager=mock_state_manager,
        config_manager=mock_config_manager,
        line_bot_api=mock_line_bot_api,
        channel_access_token="dummy_token",
        parent_folder_id="dummy_parent_id"
    )

    mock_state_manager.consume_pending_upload.assert_called_once_with("U12345")
    mock_download.assert_not_called()
    mock_gdrive_instance.find_or_create_folder.assert_not_called()
    mock_gdrive_instance.upload_file.assert_not_called()