# Standard Library Imports
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, ANY

# Third-party Imports
import pytest
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, UserSource,
    DeliveryContext
)
# --- Import handler ---
from src.handlers.text_message_handler import handle_text_message
from tests.test_helpers import create_mock_event

class TestTextMessagesAndNotes:
    """
    Tests the logic for processing text messages, including session
    creation and note-taking functionalities, by directly testing the handler.
    """
    @pytest.mark.asyncio
    async def test_handles_secret_code_and_starts_session(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """Tests that a secret code message correctly starts a user session."""
        text_message = TextMessageContent(id="123", text="#s1", quote_token="q_token_1")
        event = create_mock_event("U123_any_user", text_message)

        # --- Replace process_webhook_event with directly Handler---
        await handle_text_message(
            event, mock_state_manager, mock_config_manager, mock_gdrive_service,
            mock_line_bot_api, "dummy_parent_id"
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
            
        await handle_text_message(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, "dummy_parent_id"
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
            
        await handle_text_message(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, "dummy_parent_id"
        )

        assert mock_gdrive_service.find_or_create_folder.call_count == 2
        mock_gdrive_service.append_text_to_file.assert_called_once_with(
            ANY,
            "This is a follow-up note.",
            "daily_folder_id"
        )
        
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
            
        await handle_text_message(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, "dummy_parent_id"
        )
        
        mock_state_manager.set_pending_upload.assert_called_once_with("U789_no_space", "Group_A")
        mock_gdrive_service.append_text_to_file.assert_called_once()
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
        
        await handle_text_message(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, "dummy_parent_id"
        )

        mock_state_manager.get_active_group.assert_called_once_with("U456_no_session")
        mock_gdrive_service.append_text_to_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_longer_secret_code_correctly(
        self, mock_config_manager, mock_state_manager, mock_line_bot_api, mock_gdrive_service
    ):
        """
        Tests that when multiple codes could match the start of a message (e.g., #s1 and #s10),
        the longest matching code is chosen.
        """
        # Arrange: Add a longer, more specific code to the mock config
        mock_config_manager.get_all_secret_codes.return_value = {
            "#s1": "Group_A",
            "#s10": "Group_Ten"
        }
        
        text_message = TextMessageContent(id="t_longer", text="#s10 This is for group ten.", quote_token="q_token_longer")
        event = create_mock_event("U_longer_code_user", text_message)
            
        # Act
        await handle_text_message(
            event, mock_state_manager, mock_config_manager, 
            mock_gdrive_service, mock_line_bot_api, "dummy_parent_id"
        )

        # Assert: Ensure the session is started for the correct (longer) code
        mock_state_manager.set_pending_upload.assert_called_once_with("U_longer_code_user", "Group_Ten")
        
        # Assert: Ensure the note is extracted correctly after the longer code
        mock_gdrive_service.append_text_to_file.assert_called_once()
        args, kwargs = mock_gdrive_service.append_text_to_file.call_args
        extracted_note = args[1]
        assert extracted_note == "This is for group ten."