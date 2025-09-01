# Standard Library Imports
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch, call, ANY

# Third-party Imports
import pytest
import aiohttp
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent, UserSource,
    DeliveryContext, ContentProvider, MemberLeftEvent, GroupSource, LeftMembers
)

# Local Application Imports
from src.config_manager import ConfigManager
from src.state_manager import StateManager
from src.webhook_processor import process_webhook_event, download_image_content

# Helper function 
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

# --- Fixtures ---

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

# --- Tests ---

class TestImageMessages:
    """Tests the handling of incoming image message events."""
    @pytest.mark.asyncio
    @patch('src.webhook_processor.download_image_content')
    async def test_handles_image_when_session_is_active(
        self, mock_download, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """Tests that an image is uploaded to a daily subfolder when a session is active."""
        # Arrange
        mock_state_manager.get_active_group.return_value = "Group_A"
        mock_download.return_value = b'fake-image-bytes'
        
        with patch('src.webhook_processor.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 8, 30)
            
            mock_gdrive_service.find_or_create_folder.side_effect = ["group_folder_id", "daily_folder_id"]
            
            image_message = ImageMessageContent(id="msg_abc", quote_token="q_token_2", content_provider=ContentProvider(type="line"))
            event = create_mock_event("U123_any_user", image_message)
            
            # Act
            await process_webhook_event(
                event, mock_state_manager, mock_config_manager, mock_gdrive_service,
                mock_line_bot_api, "dummy_token", "dummy_parent_id"
            )
            
            # Assert
            mock_state_manager.get_active_group.assert_called_once_with("U123_any_user")
            mock_download.assert_called_once()
            
            expected_calls = [
                call("Group_A", parent_folder_id="dummy_parent_id"),
                call("2025-08-30", parent_folder_id="group_folder_id")
            ]
            mock_gdrive_service.find_or_create_folder.assert_has_calls(expected_calls)
            
            mock_gdrive_service.upload_file.assert_called_once_with(
                f"{event.message.id}.jpg", b'fake-image-bytes', "daily_folder_id"
            )
            mock_state_manager.refresh_session.assert_called_once_with("U123_any_user")
        
    @pytest.mark.asyncio
    @patch('src.webhook_processor.download_image_content')
    async def test_ignores_image_when_no_active_session(
            self, mock_download, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
        ):
        """Tests that an image is ignored if the user has no active session."""
        mock_state_manager.get_active_group.return_value = None
        image_message = ImageMessageContent(id="msg_def", quote_token="q_token_3", content_provider=ContentProvider(type="line"))
        event = create_mock_event("U456_other_user", image_message)
            
        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, mock_gdrive_service,
            mock_line_bot_api, "dummy_token", "dummy_parent_id"
            )
            
        mock_state_manager.get_active_group.assert_called_once_with("U456_other_user")
        mock_download.assert_not_called()
        mock_gdrive_service.upload_file.assert_not_called()
        mock_state_manager.refresh_session.assert_not_called()

class TestTextMessagesAndNotes:
    """Tests the logic for processing text messages, including session
    creation and note-taking functionalities.
    """
    @pytest.mark.asyncio
    async def test_handles_secret_code_and_starts_session(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """Tests that a secret code message correctly starts a user session."""
        text_message = TextMessageContent(id="123", text="#s1", quote_token="q_token_1")
        event = create_mock_event("U123_any_user", text_message)
        
        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, mock_gdrive_service,
            mock_line_bot_api, "dummy_token", "dummy_parent_id"
        )
        
        mock_state_manager.set_pending_upload.assert_called_once_with("U123_any_user", "Group_A")
        mock_line_bot_api.reply_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_secret_code_with_initial_note(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """
        Tests that a text message containing a secret code and a note starts a session
        and extracts the note correctly.
        """
        text_message = TextMessageContent(id="t1", text="#s1 This is an initial note.", quote_token="q_token_note_1")
        event = create_mock_event("U123_note_user", text_message)
            
        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, 
            "dummy_token", "dummy_parent_id"
            )

        mock_state_manager.set_pending_upload.assert_called_once_with("U123_note_user", "Group_A")
        mock_gdrive_service.append_text_to_file.assert_called_once_with(
            f"{datetime.now().strftime('%Y-%m-%d')}_notes.txt",
            "This is an initial note.",
            mock_gdrive_service.find_or_create_folder.return_value
        )
        mock_line_bot_api.reply_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_subsequent_note_with_active_session(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """
        Tests that a simple text message is treated as a note when a session is active.
        """
        mock_state_manager.get_active_group.return_value = "Group_A"
        text_message = TextMessageContent(id="t2", text="This is a follow-up note.", quote_token="q_token_note_2")
        event = create_mock_event("U123_note_user", text_message)
        mock_gdrive_service.find_or_create_folder.side_effect = ["group_folder_id", "daily_folder_id"]
            
        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, 
            "dummy_token", "dummy_parent_id"
            )

        # Assert that find_or_create_folder was called twice
        assert mock_gdrive_service.find_or_create_folder.call_count == 2
        
        # FIX: Assert that append_text_to_file is called with the ID of the *daily* folder
        mock_gdrive_service.append_text_to_file.assert_called_once_with(
            ANY, # We don't care about the filename in this check
            "This is a follow-up note.",
            "daily_folder_id" # This must be the ID of the nested daily folder
        )
        mock_state_manager.refresh_session.assert_called_once_with("U123_note_user")

    @pytest.mark.asyncio
    async def test_handles_secret_code_without_space_before_note(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """
        Tests that a session is started and the note is correctly extracted
        even when there is no space between the secret code and the note.
        """
        text_message = TextMessageContent(id="t4", text="#s1Urgent meeting.", quote_token="q_token_note_4")
        event = create_mock_event("U789_no_space", text_message)
            
        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, 
            "dummy_token", "dummy_parent_id"
            )
        # A session should be started
        mock_state_manager.set_pending_upload.assert_called_once_with("U789_no_space", "Group_A")
        # The note should be saved
        mock_gdrive_service.append_text_to_file.assert_called_once()
        # Check that the note text is correctly extracted
        args, kwargs = mock_gdrive_service.append_text_to_file.call_args
        extracted_note = args[1]
        assert extracted_note == "Urgent meeting."

    @pytest.mark.asyncio
    async def test_ignores_text_with_no_active_session(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """
        Tests that a text message not containing a command or secret code is ignored
        if no session is active.
        """
        mock_state_manager.get_active_group.return_value = None
        text_message = TextMessageContent(id="t3", text="This note should be ignored.", quote_token="q_token_note_3")
        event = create_mock_event("U456_no_session", text_message)
        
        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, 
            "dummy_token", "dummy_parent_id"
            )

        mock_state_manager.get_active_group.assert_called_once_with("U456_no_session")
        mock_gdrive_service.append_text_to_file.assert_not_called()

class TestGeneralEventHandling:
    """Tests the overall behavior of the webhook processor, such as
    handling non-message events and edge cases like duplicate events.
    """
    @pytest.mark.asyncio
    async def test_ignores_non_message_event_gracefully(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
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
                member_left_event, mock_state_manager, mock_config_manager, 
                mock_gdrive_service, mock_line_bot_api, 
                "dummy_token", "dummy_parent_id"
            )
        except AttributeError:
            pytest.fail("process_webhook_event crashed with AttributeError on a non-message event.")

        # Assert that no message-related functions were called
        mock_state_manager.set_pending_upload.assert_not_called()
        mock_state_manager.get_active_group.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.webhook_processor.redis_client') 
    @patch('src.webhook_processor.download_image_content')
    async def test_ignores_duplicate_event_id(
        self, mock_download, mock_redis_client, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """
        Tests that if redis_client.set returns False (duplicate event),
        the function exits early and does not process the image.
        """
        mock_redis_client.set.return_value = False
        image_message = ImageMessageContent(id="duplicate_msg_id", quote_token="q_token_dup", content_provider=ContentProvider(type="line"))
        event = create_mock_event("U123_any_user", image_message)

        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, 
            "dummy_token", "dummy_parent_id"
            )

        mock_redis_client.set.assert_called_once_with("line_msg_duplicate_msg_id", "processed", nx=True, ex=60)
        mock_download.assert_not_called()
        mock_gdrive_service.upload_file.assert_not_called()
        mock_state_manager.get_active_group.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.webhook_processor.redis_client', None)
    @patch('src.webhook_processor.download_image_content')
    async def test_processes_image_normally_when_redis_is_unavailable(
        self, mock_download, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """
        Tests that the system still processes an image upload
        when the Redis client is not available (is None).
        This documents the current fallback behavior.
        """
        mock_state_manager.get_active_group.return_value = "Group_A"
        mock_download.return_value = b'fake-image-bytes'
        image_message = ImageMessageContent(id="msg_xyz", quote_token="q_token_4", content_provider=ContentProvider(type="line"))
        event = create_mock_event("U123_no_redis_user", image_message)
            
        await process_webhook_event(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, 
            "dummy_token", "dummy_parent_id"
            )
        
        mock_gdrive_service.find_or_create_folder.return_value = "dummy_folder_id"
        mock_state_manager.get_active_group.assert_called_once_with("U123_no_redis_user")
        mock_download.assert_called_once()
        mock_gdrive_service.upload_file.assert_called_once()
        mock_state_manager.refresh_session.assert_called_once_with("U123_no_redis_user")

class TestNetworkHandling:
    """Tests helper functions related to network operations, such as
    downloading content with retry logic.
    """
    @pytest.mark.asyncio
    @patch('src.webhook_processor.aiohttp.ClientSession.get')
    async def test_download_image_with_retry_on_connection_error(self, mock_session_get):
        """
        Tests that download_image_content retries on a connection error
        and succeeds on the second attempt.
        """
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
        
        mock_session_get.side_effect = [
            connector_error,          # First call: raise the error
            mock_response_successful, # Second call: return the successful response mock
        ]
        result = await download_image_content("any_image_id", "dummy_token")
        assert result == b'successful-image-bytes'
        assert mock_session_get.call_count == 2







