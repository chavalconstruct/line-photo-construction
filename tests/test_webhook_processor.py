import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from src.webhook_processor import process_webhook_event, download_image_content
from src.state_manager import StateManager
from src.config_manager import ConfigManager
import aiohttp
import os
from datetime import datetime
from linebot.v3.webhooks import (
    MessageEvent, 
    TextMessageContent,
    ImageMessageContent,
    UserSource,
    DeliveryContext,
    ContentProvider,
    MemberLeftEvent,
    GroupSource,
    LeftMembers
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
    """
    Provides a mock ConfigManager that is compatible with the latest
    note-taking and session-starting logic.
    """
    mock = MagicMock(spec=ConfigManager)
    
    # FIX: This is the primary fix.
    # Mock get_all_secret_codes() to return the dictionary our new logic needs.
    mock.get_all_secret_codes.return_value = {
        "#s1": "Group_A",
        "#s2": "Group_B" # Added for completeness
    }
    
    # Mock is_admin for tests that require admin checks.
    mock.is_admin.return_value = False # Default to False unless specified in a test
    
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
    
    # This assertion will now pass because the mock provides the necessary data.
    mock_state_manager.set_pending_upload.assert_called_once_with("U123_any_user", "Group_A")
    mock_line_bot_api.reply_message.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.datetime')
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_handles_image_when_session_is_active(
    mock_download, mock_gdrive_service_class, mock_datetime, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Test 2: Tests that receiving an image calls state_manager.get_active_group()
    and proceeds to upload into a daily subfolder.
    """
    # Arrange: Simulate that a session is active for this user
    mock_state_manager.get_active_group.return_value = "Group_A"
    mock_download.return_value = b'fake-image-bytes'
    
    # --- TDD Changes Start Here ---

    # 1. Mock datetime to control the date for our test
    mock_datetime.now.return_value = datetime(2025, 8, 30)
    
    mock_gdrive_instance = mock_gdrive_service_class.return_value
    
    # 2. Use side_effect to return different folder IDs on each call
    mock_gdrive_instance.find_or_create_folder.side_effect = [
        "group_folder_id",  # First call returns the main group folder ID
        "daily_folder_id"   # Second call returns the new daily subfolder ID
    ]
    
    # --- TDD Changes End Here ---

    image_message = ImageMessageContent(id="msg_abc", quote_token="q_token_2", content_provider=ContentProvider(type="line"))
    event = create_mock_event("U123_any_user", image_message)
    
    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")
    
    # Assert that the system checked for an active group with the correct user ID
    mock_state_manager.get_active_group.assert_called_once_with("U123_any_user")
    mock_download.assert_called_once()

    # --- TDD Assertion Changes ---

    # 3. Assert that find_or_create_folder was called twice with the correct arguments
    expected_calls = [
        call("Group_A", parent_folder_id="dummy_parent_id"),
        call("2025-08-30", parent_folder_id="group_folder_id")
    ]
    mock_gdrive_instance.find_or_create_folder.assert_has_calls(expected_calls)
    assert mock_gdrive_instance.find_or_create_folder.call_count == 2

    # Assert that upload_file is called with the final daily folder ID
    mock_gdrive_instance.upload_file.assert_called_once_with(
        f"{event.message.id}.jpg", 
        b'fake-image-bytes', 
        "daily_folder_id"
    )

    # --- End of Assertion Changes ---
    
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

@pytest.mark.asyncio
@patch('src.webhook_processor.redis_client') # <-- Mock redis_client
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_ignores_duplicate_event_id(
    mock_download, mock_gdrive_service_class, mock_redis_client,
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that if redis_client.set returns False (duplicate event),
    the function exits early and does not process the image.
    """
    mock_redis_client.set.return_value = False

    image_message = ImageMessageContent(id="duplicate_msg_id", quote_token="q_token_dup", content_provider=ContentProvider(type="line"))
    event = create_mock_event("U123_any_user", image_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_redis_client.set.assert_called_once_with("line_msg_duplicate_msg_id", "processed", nx=True, ex=60)
    mock_download.assert_not_called()
    mock_gdrive_service_class.return_value.upload_file.assert_not_called()
    mock_state_manager.get_active_group.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.redis_client', None) # <-- Mock redis_client is None
@patch('src.webhook_processor.GoogleDriveService')
@patch('src.webhook_processor.download_image_content')
async def test_processes_image_normally_when_redis_is_unavailable(
    mock_download, mock_gdrive_service_class,
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that the system still processes an image upload
    when the Redis client is not available (is None).
    This documents the current fallback behavior.
    """
    
    mock_state_manager.get_active_group.return_value = "Group_A"
    mock_download.return_value = b'fake-image-bytes'
    mock_gdrive_instance = mock_gdrive_service_class.return_value
    mock_gdrive_instance.find_or_create_folder.return_value = "dummy_folder_id"


    image_message = ImageMessageContent(id="msg_xyz", quote_token="q_token_4", content_provider=ContentProvider(type="line"))
    event = create_mock_event("U123_no_redis_user", image_message)

   
    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

   
    mock_state_manager.get_active_group.assert_called_once_with("U123_no_redis_user")
    mock_download.assert_called_once()
    mock_gdrive_instance.upload_file.assert_called_once()
    mock_state_manager.refresh_session.assert_called_once_with("U123_no_redis_user")

@pytest.mark.asyncio
# 1. Change the patch target to be more specific
@patch('src.webhook_processor.aiohttp.ClientSession.get')
async def test_download_image_with_retry_on_connection_error(mock_session_get):
    """
    Tests that download_image_content retries on a connection error
    and succeeds on the second attempt.
    """
    # 2. Arrange: Create the required objects for the side_effect
    
    # The successful response mock (must be a valid async context manager)
    mock_response_successful = AsyncMock()
    mock_response_successful.status = 200
    mock_response_successful.read = AsyncMock(return_value=b'successful-image-bytes')
    mock_response_successful.__aenter__.return_value = mock_response_successful
    mock_response_successful.__aexit__ = AsyncMock(return_value=None)
    
    # The error to be raised on the first attempt
    mock_connection_key = MagicMock() 
    os_error = OSError(101, "Simulated Network is unreachable")
    connector_error = aiohttp.ClientConnectorError(mock_connection_key, os_error)

    # 3. Configure the side_effect directly on the mocked 'get' method
    mock_session_get.side_effect = [
        connector_error,          # First call: raise the error
        mock_response_successful, # Second call: return the successful response mock
    ]

    # 4. Act: Call the function under test
    result = await download_image_content("any_image_id", "dummy_token")

    # 5. Assert: Verify the outcome
    assert result == b'successful-image-bytes'
    assert mock_session_get.call_count == 2

# The test case now has the classes it needs
@pytest.mark.asyncio
async def test_ignores_non_message_event_gracefully(
    mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that a non-MessageEvent is ignored gracefully without crashing.
    """
    # This code will now work correctly
    member_left_event = MemberLeftEvent(
        source=GroupSource(group_id="G123"), # user_id is not needed here
        left=LeftMembers(members=[UserSource(user_id="U123")]),
        timestamp=1673377200000,
        mode="active",
        webhook_event_id="01GA0000000000000000000000000000",
        delivery_context=DeliveryContext(is_redelivery=False)
    )

    try:
        await process_webhook_event(
            member_left_event,
            mock_state_manager,
            mock_config_manager,
            mock_line_bot_api,
            "dummy_token",
            "dummy_parent_id"
        )
    except AttributeError:
        pytest.fail("process_webhook_event crashed with AttributeError on a non-message event.")

    # Assert that no message-related functions were called
    mock_state_manager.set_pending_upload.assert_not_called()
    mock_state_manager.get_active_group.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
async def test_handles_secret_code_with_initial_note(
    mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that a text message containing a secret code and a note starts a session
    and extracts the note correctly.
    """
    mock_gdrive_instance = mock_gdrive_service_class.return_value
    text_message = TextMessageContent(id="t1", text="#s1 This is an initial note.", quote_token="q_token_note_1")
    event = create_mock_event("U123_note_user", text_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_state_manager.set_pending_upload.assert_called_once_with("U123_note_user", "Group_A")
    
    mock_gdrive_instance.append_text_to_file.assert_called_once_with(
        f"{datetime.now().strftime('%Y-%m-%d')}_notes.txt",
        "This is an initial note.",
        mock_gdrive_instance.find_or_create_folder.return_value
    )
    mock_line_bot_api.reply_message.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
async def test_handles_subsequent_note_with_active_session(
    mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that a simple text message is treated as a note when a session is active.
    """
    mock_state_manager.get_active_group.return_value = "Group_A"
    mock_gdrive_instance = mock_gdrive_service_class.return_value

    text_message = TextMessageContent(id="t2", text="This is a follow-up note.", quote_token="q_token_note_2")
    event = create_mock_event("U123_note_user", text_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_state_manager.get_active_group.assert_called_once_with("U123_note_user")
    mock_gdrive_instance.append_text_to_file.assert_called_once()
    mock_state_manager.refresh_session.assert_called_once_with("U123_note_user")


@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
async def test_ignores_text_with_no_active_session(
    mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that a text message not containing a command or secret code is ignored
    if no session is active.
    """
    mock_state_manager.get_active_group.return_value = None
    mock_gdrive_instance = mock_gdrive_service_class.return_value

    text_message = TextMessageContent(id="t3", text="This note should be ignored.", quote_token="q_token_note_3")
    event = create_mock_event("U456_no_session", text_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    mock_state_manager.get_active_group.assert_called_once_with("U456_no_session")
    mock_gdrive_instance.append_text_to_file.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.GoogleDriveService')
async def test_handles_secret_code_without_space_before_note(
    mock_gdrive_service_class, mock_config_manager, mock_state_manager, mock_line_bot_api
):
    """
    Tests that a session is started and the note is correctly extracted
    even when there is no space between the secret code and the note.
    """
    mock_gdrive_instance = mock_gdrive_service_class.return_value
    text_message = TextMessageContent(id="t4", text="#s1Urgent meeting.", quote_token="q_token_note_4")
    event = create_mock_event("U789_no_space", text_message)

    await process_webhook_event(event, mock_state_manager, mock_config_manager, mock_line_bot_api, "dummy_token", "dummy_parent_id")

    # A session should be started
    mock_state_manager.set_pending_upload.assert_called_once_with("U789_no_space", "Group_A")
    # The note should be saved
    mock_gdrive_instance.append_text_to_file.assert_called_once()
    # Check that the note text is correctly extracted
    args, kwargs = mock_gdrive_instance.append_text_to_file.call_args
    extracted_note = args[1]
    assert extracted_note == "Urgent meeting."