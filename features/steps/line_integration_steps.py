from behave import *
import json
from unittest.mock import patch, MagicMock
from src.webhook_processor import process_webhook_event

@given('a mapping of LINE user IDs to application users')
def step_impl(context):
    context.line_user_map = json.loads(context.text)

@given('user configurations for Google Drive folders')
def step_impl(context):
    context.user_configs = json.loads(context.text)

@when('the system receives a LINE webhook for an image message from user "{line_user_id}"')
def step_impl(context, line_user_id):
    context.mock_image_bytes = b'fake image data from mocked line api'
    with patch('src.webhook_processor.GoogleDriveService') as mock_gdrive_service_class, \
         patch('src.webhook_processor.LineBotApi') as mock_line_api_class:

        mock_gdrive_instance = mock_gdrive_service_class.return_value
        context.mock_gdrive_service = mock_gdrive_instance
        mock_gdrive_instance.find_or_create_folder.return_value = 'mock_folder_id'

        mock_line_api_instance = mock_line_api_class.return_value
        response_mock = MagicMock()
        response_mock.content = context.mock_image_bytes
        mock_line_api_instance.get_message_content.return_value = response_mock
        context.mock_line_api = mock_line_api_instance

        mock_webhook_body = f"""
        {{
            "events": [
                {{
                    "type": "message",
                    "message": {{ "type": "image", "id": "msg_id_9876" }},
                    "source": {{ "type": "user", "userId": "{line_user_id}" }}
                }}
            ]
        }}
        """
        webhook_data = json.loads(mock_webhook_body)
        first_event = webhook_data["events"][0]
        
        process_webhook_event(
            event=first_event,
            line_user_map=context.line_user_map,
            user_configs=context.user_configs
        )

@then('the image from "{app_user}" should be uploaded to her assigned group folder')
def step_impl(context, app_user):
    # --- NEW LOGIC ---
    # Calculate the expected group name based on the setup in the 'Given' step.
    expected_group_name = context.user_configs.get(app_user)
    
    context.mock_line_api.get_message_content.assert_called_once_with("msg_id_9876")
    
    # Assert that the Google Drive service was called with the CORRECTLY DEDUCED group name.
    context.mock_gdrive_service.find_or_create_folder.assert_called_once_with(expected_group_name)
    
    context.mock_gdrive_service.upload_file.assert_called_once_with(
        file_name="msg_id_9876.jpg",
        file_content=context.mock_image_bytes,
        folder_id='mock_folder_id'
    )