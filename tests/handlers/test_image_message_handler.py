# Standard Library Imports
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch, call

# Third-party Imports
import pytest
import aiohttp
from linebot.v3.webhooks import (
    ImageMessageContent, ContentProvider
)

# Local Application Imports
from src.state_manager import StateManager
# --- 1. Import handler and function test---
from src.handlers.image_message_handler import handle_image_message, download_image_content

# --- Import Helper and Fixtures ---
from tests.test_helpers import create_mock_event


class TestImageMessages:
    """Tests the handling of incoming image message events."""
    @pytest.mark.asyncio
    @patch('src.handlers.image_message_handler.download_image_content')
    async def test_handles_image_when_session_is_active(
        self, mock_download, mock_state_manager, mock_gdrive_service
    ):
        """Tests that an image is uploaded to a daily subfolder when a session is active."""
        # Arrange
        mock_state_manager.get_active_group.return_value = "Group_A"
        mock_download.return_value = b'fake-image-bytes'
        
        # Patch datetime 
        with patch('src.handlers.image_message_handler.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 8, 30)
            
            mock_gdrive_service.find_or_create_folder.side_effect = ["group_folder_id", "daily_folder_id"]
            
            image_message = ImageMessageContent(id="msg_abc", quote_token="q_token_2", content_provider=ContentProvider(type="line"))
            event = create_mock_event("U123_any_user", image_message)
            
            # --- Use directly Handler ---
            await handle_image_message(
                event, mock_state_manager, mock_gdrive_service,
                "dummy_token", "dummy_parent_id"
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
                    
    @pytest.mark.asyncio
    @patch('src.handlers.image_message_handler.download_image_content')
    async def test_ignores_image_when_no_active_session(
            self, mock_download, mock_state_manager, mock_gdrive_service
        ):
        """Tests that an image is ignored if the user has no active session."""
        mock_state_manager.get_active_group.return_value = None
        image_message = ImageMessageContent(id="msg_def", quote_token="q_token_3", content_provider=ContentProvider(type="line"))
        event = create_mock_event("U456_other_user", image_message)
            
        await handle_image_message(
            event, mock_state_manager, mock_gdrive_service,
            "dummy_token", "dummy_parent_id"
        )
            
        mock_state_manager.get_active_group.assert_called_once_with("U456_other_user")
        mock_download.assert_not_called()
        mock_gdrive_service.upload_file.assert_not_called()
        
class TestNetworkHandling:
    """Tests helper functions related to network operations, such as
    downloading content with retry logic.
    """
    @pytest.mark.asyncio
    @patch('src.handlers.image_message_handler.aiohttp.ClientSession.get')
    async def test_download_image_with_retry_on_connection_error(self, mock_session_get):
        """
        Tests that download_image_content retries on a connection error
        and succeeds on the second attempt.
        """
        mock_response_successful = AsyncMock()
        mock_response_successful.status = 200
        mock_response_successful.read = AsyncMock(return_value=b'successful-image-bytes')
        mock_response_successful.__aenter__.return_value = mock_response_successful
        mock_response_successful.__aexit__ = AsyncMock(return_value=None)
        
        mock_connection_key = MagicMock() 
        os_error = OSError(101, "Simulated Network is unreachable")
        connector_error = aiohttp.ClientConnectorError(mock_connection_key, os_error)
        
        mock_session_get.side_effect = [
            connector_error,
            mock_response_successful,
        ]
        # --- 6. call directly download_image_content  ---
        result = await download_image_content("any_image_id", "dummy_token")
        assert result == b'successful-image-bytes'
        assert mock_session_get.call_count == 2