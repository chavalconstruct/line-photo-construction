from behave import *
import json
from src.webhook_processor import process_webhook_event
from features.steps.classification_steps import step_impl as a_folder_should_be_created_step
from unittest.mock import patch

@given('the LINE user ID "{line_user_id}" is mapped to the application user "{app_user}"')
def step_impl(context, line_user_id, app_user):
    """
    Stores a mapping between a LINE user ID and an internal application username.
    """
    if not hasattr(context, 'line_user_map'):
        context.line_user_map = {}
    context.line_user_map[line_user_id] = app_user

@when('the system receives a LINE webhook for an image message from user "{line_user_id}"')
def step_impl(context, line_user_id):
    """
    Simulates receiving a webhook and calls the real processing function.
    """
    with patch('src.webhook_processor.GoogleDriveService') as mock_gdrive_service_class:
        # Store the MOCK INSTANCE in the context so we can check it later
        mock_service_instance = mock_gdrive_service_class.return_value
        context.mock_gdrive_service = mock_service_instance

        mock_service_instance.find_or_create_folder.return_value = 'mock_folder_id'

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

@then('the image content should be queued for upload to "{group_name}"')
def step_impl(context, group_name):
    """
    Checks that the GoogleDriveService.upload_file method was called
    with the correct parameters.
    """
    context.mock_gdrive_service.find_or_create_folder.assert_called_once_with(group_name)

    context.mock_gdrive_service.upload_file.assert_called_once_with(
        file_name="msg_id_9876.jpg",
        file_content=b'dummy image content from webhook',
        folder_id='mock_folder_id' 
    )

    