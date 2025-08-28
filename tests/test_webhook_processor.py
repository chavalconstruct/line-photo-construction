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
    """Helper function to create a valid MessageEvent object for tests."""
    return MessageEvent(
        reply_token=reply_token,
        source=UserSource(user_id=user_id),
        message=message_content,
        timestamp=1673377200000,
        mode="active",
        webhook_event_id="01GA0000000000000000000000000000",
        delivery_context=DeliveryContext(is_redelivery=False)
    )

# --- Fixtures ---
@pytest.fixture
def mock_config_manager():
    mock = MagicMock(spec=ConfigManager)
    mock.get_group_from_secret_code.side_effect = lambda code: "Group_A" if code == "#s1" else None
    return mock

@pytest.fixture
def mock_state_manager():
    # We now mock the new methods for StateManager
    mock = MagicMock(spec=StateManager)
    # Configure get_active_group to return a group name for a specific user
    mock.get_active_group.side_effect = lambda user_id: "Group_A" if user_id == "U12345" else None
    return mock

@pytest.fixture
def mock_line_bot_api():
    api_mock = AsyncMock()
    api_mock.reply_message = AsyncMock()
    return api_mock

# --- NEW AND UPDATED TESTS FOR SESSION LOGIC ---

@pytest.mark.asyncio
async def test_handles_secret_code_and_starts_session(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 1: Handles a valid secret code, sets state, and DOES NOT reply."""
    text_message = TextMessageContent(id="123", text="#s1", quote_token="q_token_1")
    event = create_mock_event("U12345", text_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    # Verify state is set
    mock_state_manager.set_pending_upload.assert_called_once_with("U12345", "Group_A")
    # CRUCIAL: Verify that no reply is sent
    mock_line_bot_api.reply_message.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_handles_image_when_session_is_active(
    mock_download, mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 2: Handles an image when a user has an active session and refreshes it."""
    mock_download.return_value = b'fake-image-bytes'
    mock_gdrive_instance = mock_gdrive_service_class.return_value
    
    image_message = ImageMessageContent(id="msg_abc", quote_token="q_token_2", content_provider=ContentProvider(type="line"))
    # User U12345 has an active session based on our mock_state_manager setup
    event = create_mock_event("U12345", image_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    # Verify the active group was checked
    mock_state_manager.get_active_group.assert_called_once_with("U12345")
    # Verify upload process was triggered
    mock_download.assert_called_once()
    mock_gdrive_instance.upload_file.assert_called_once()
    # CRUCIAL: Verify the session was refreshed to keep it alive
    mock_state_manager.refresh_session.assert_called_once_with("U12345")

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_ignores_image_when_no_active_session(
    mock_download, mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 3: Ignores an image when the user has no active session."""
    image_message = ImageMessageContent(id="msg_def", quote_token="q_token_3", content_provider=ContentProvider(type="line"))
    # User U67890 does NOT have an active session based on our mock_state_manager setup
    event = create_mock_event("U67890", image_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    # Verify the active group was checked
    mock_state_manager.get_active_group.assert_called_once_with("U67890")
    # CRUCIAL: Verify no upload happened
    mock_download.assert_not_called()
    mock_gdrive_service_class.return_value.upload_file.assert_not_called()
    # CRUCIAL: Verify session was NOT refreshed
    mock_state_manager.refresh_session.assert_not_called()

# We can keep admin tests as they are not affected by this change
@pytest.mark.asyncio
async def test_admin_successfully_adds_code(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Admin test: An admin user successfully adds a new secret code."""
    command_text = "add code #s3 for group Group_C"
    text_message = TextMessageContent(id="admin_msg_1", text=command_text, quote_token="q_token_4")
    mock_config_manager.is_admin.return_value = True # Ensure this user is seen as admin
    event = create_mock_event("U_ADMIN", text_message, reply_token="admin_reply_token")

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_config_manager.add_secret_code.assert_called_once_with("#s3", "Group_C")
    mock_line_bot_api.reply_message.assert_called_once()