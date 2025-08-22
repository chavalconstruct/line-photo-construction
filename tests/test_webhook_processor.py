import pytest
from unittest.mock import patch, MagicMock
from src.webhook_processor import process_webhook_event

class TestWebhookProcessor:
    def test_process_event_identifies_user_and_group(self):
        """
        Ensures the function correctly maps a LINE user ID to a user,
        finds their group, and prepares for upload.
        """
        event_data = {
            "source": {"userId": "U12345abcde"},
            "message": {"type": "image", "id": "msg_id_9876"}
        }
        line_user_map = {"U12345abcde": "Somchai"}
        user_configs = {"Somchai": "Group A"}

        # --- use patch for simulate working ---
        with patch('src.webhook_processor.LineBotApi') as mock_line_api_class, \
             patch('src.webhook_processor.GoogleDriveService') as mock_gdrive_service_class:

            # 1. config Mock for LineBotApi
            mock_line_api_instance = mock_line_api_class.return_value
            response_mock = MagicMock()
            response_mock.content = b'dummy image content'
            mock_line_api_instance.get_message_content.return_value = response_mock

            # 2. config Mock for GoogleDriveService
            mock_gdrive_instance = mock_gdrive_service_class.return_value
            mock_gdrive_instance.find_or_create_folder.return_value = 'mock_folder_id_123'
            mock_gdrive_instance.upload_file.return_value = 'mock_file_id_456'

            # 3. call function to test
            result = process_webhook_event(
                event=event_data,
                line_user_map=line_user_map,
                user_configs=user_configs
            )
            
            # 4. check result and call Mock
            mock_line_api_instance.get_message_content.assert_called_once_with("msg_id_9876")
            mock_gdrive_instance.find_or_create_folder.assert_called_once_with("Group A")
            mock_gdrive_instance.upload_file.assert_called_once()
            assert result == 'mock_file_id_456'