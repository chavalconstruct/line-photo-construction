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
    ContentProvider,
)

# Helper function remains the same
def create_mock_event(user_id, message_content, reply_token="dummy_reply_token"):
    return MessageEvent(
        reply_token=reply_token,
        source=UserSource(user_id=user_id),
        message=message_content,
        timestamp=1673377200000,
        mode="active",
        webhook_event_id="01GA0000000000000000000000000000",
        delivery_context=DeliveryContext(is_redelivery=False)
    )

@pytest.fixture
def mock_config_manager():
    # We no longer need to mock get_app_user
    mock = MagicMock(spec=ConfigManager)
    mock.get_group_from_secret_code.side_effect = lambda code: "Group_A" if code == "#s1" else None
    mock.is_admin.side_effect = lambda user_id: True if user_id == "U_ADMIN" else False
    return mock

@pytest.fixture
def mock_state_manager():
    return MagicMock(spec=StateManager)

@pytest.fixture
def mock_line_bot_api():
    api_mock = AsyncMock()
    api_mock.reply_message = AsyncMock()
    return api_mock

@pytest.mark.asyncio
async def test_handles_secret_code_and_starts_session(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Test 1: Tests that receiving a secret code calls state_manager.set_pending_upload()
    with the user_id from the event.
    """
    text_message = TextMessageContent(id="123", text="#s1", quote_token="q_token_1")
    event = create_mock_event("U123_any_user", text_message)
    
    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")
    
    # Assert that a session is started for the correct user ID
    mock_state_manager.set_pending_upload.assert_called_once_with("U123_any_user", "Group_A")
    mock_line_bot_api.reply_message.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_handles_image_when_session_is_active(
    mock_download, mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Test 2: Tests that receiving an image calls state_manager.get_active_group()
    and proceeds to upload.
    """
    # Arrange: Simulate that a session is active for this user
    mock_state_manager.get_active_group.return_value = "Group_A"
    mock_download.return_value = b'fake-image-bytes'
    mock_gdrive_instance = mock_gdrive_service_class.return_value
    
    image_message = ImageMessageContent(id="msg_abc", quote_token="q_token_2", content_provider=ContentProvider(type="line"))
    event = create_mock_event("U123_any_user", image_message)
    
    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")
    
    # Assert that the system checked for an active group with the correct user ID
    mock_state_manager.get_active_group.assert_called_once_with("U123_any_user")
    mock_download.assert_called_once()
    mock_gdrive_instance.upload_file.assert_called_once()
    # Assert that the session was refreshed after upload
    mock_state_manager.refresh_session.assert_called_once_with("U123_any_user")

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_ignores_image_when_no_active_session(
    mock_download, mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that an image from a user with no active session is ignored.
    """
    # Arrange: Simulate that NO session is active for this user
    mock_state_manager.get_active_group.return_value = None
    
    image_message = ImageMessageContent(id="msg_def", quote_token="q_token_3", content_provider=ContentProvider(type="line"))
    event = create_mock_event("U456_other_user", image_message)
    
    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")
    
    mock_state_manager.get_active_group.assert_called_once_with("U456_other_user")
    mock_download.assert_not_called()
    mock_gdrive_service_class.return_value.upload_file.assert_not_called()
    mock_state_manager.refresh_session.assert_not_called()