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

# REVISED HELPER: Now includes reply_token
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

# --- Fixtures (remain the same) ---
@pytest.fixture
def mock_config_manager():
    mock = MagicMock(spec=ConfigManager)
    mock.get_group_from_secret_code.side_effect = lambda code: "Group_A" if code == "#s1" else None
    mock.get_app_user.return_value = "Alice"
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

# --- ALL TESTS BELOW ARE CORRECTED ---

@pytest.mark.asyncio
async def test_handles_secret_code_and_sets_state(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 1: Handles a valid secret code and sets the user's state."""
    # FIX: Added quote_token
    text_message = TextMessageContent(id="123", text="#s1", quote_token="q_token_1")
    event = create_mock_event("U12345", text_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

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
    mock_state_manager.consume_pending_upload.return_value = "Group_A"

    # FIX: Added quote_token
    image_message = ImageMessageContent(id="msg_abc", quote_token="q_token_2", content_provider=ContentProvider(type="line"))
    event = create_mock_event("U12345", image_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_state_manager.consume_pending_upload.assert_called_once_with("U12345")
    mock_download.assert_called_once()
    mock_gdrive_instance.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_admin_successfully_adds_code(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 3: An admin user successfully adds a new secret code."""
    command_text = "add code #s3 for group Group_C"
    # FIX: Added quote_token
    text_message = TextMessageContent(id="admin_msg_1", text=command_text, quote_token="q_token_3")
    # FIX: Moved reply_token to the event object
    event = create_mock_event("U_ADMIN", text_message, reply_token="admin_reply_token")

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_config_manager.is_admin.assert_called_once_with("U_ADMIN")
    mock_config_manager.add_secret_code.assert_called_once_with("#s3", "Group_C")
    mock_config_manager.save_config.assert_called_once()
    mock_line_bot_api.reply_message.assert_called_once()

@pytest.mark.asyncio
async def test_non_admin_is_denied(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 4: A non-admin user is denied from using an admin command."""
    command_text = "remove code #s1"
    # FIX: Added quote_token
    text_message = TextMessageContent(id="user_msg_1", text=command_text, quote_token="q_token_4")
    # FIX: Moved reply_token to the event object
    event = create_mock_event("U_NON_ADMIN", text_message, reply_token="user_reply_token")

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_config_manager.is_admin.assert_called_once_with("U_NON_ADMIN")
    mock_config_manager.remove_secret_code.assert_not_called()
    mock_config_manager.save_config.assert_not_called()
    mock_line_bot_api.reply_message.assert_called_once()

@pytest.mark.asyncio
async def test_ignores_non_command_non_secret_code_text(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """Test 5: Ignores regular text that is neither a command nor a secret code."""
    # FIX: Added quote_token
    text_message = TextMessageContent(id="msg_hello", text="hello world", quote_token="q_token_5")
    event = create_mock_event("U12345", text_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_config_manager.get_group_from_secret_code.assert_called_with("hello world")
    mock_state_manager.set_pending_upload.assert_not_called()
    mock_line_bot_api.reply_message.assert_not_called()