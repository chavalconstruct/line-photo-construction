"""
This module contains the logic for processing webhook events from the LINE API.
"""
import os
from linebot import LineBotApi
from src.google_drive_uploader import GoogleDriveService

# It's a good practice to get secrets from environment variables
# For now, the test will mock this, so the actual value doesn't matter in the test.
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "dummy_token")

def process_webhook_event(event, line_user_map, user_configs):
    """
    Processes a single event from a LINE webhook payload.

    It identifies the user and their group, then triggers an upload
    to Google Drive.
    """
    # Ensure the message is an image
    if event.get("message", {}).get("type") != "image":
        return None

    # Extract the LINE User ID from the event
    line_user_id = event.get("source", {}).get("userId")
    if not line_user_id:
        return None

    # Find the application user from the mapping
    app_user = line_user_map.get(line_user_id)
    if not app_user:
        # This handles the 'test_process_event_with_unknown_user_returns_none' case
        return None

    # Find the user's group
    group = user_configs.get(app_user)
    if not group:
        return None

    # Extract the image message ID
    image_message_id = event.get("message", {}).get("id")

    # REPLACED the dummy content line with a real API call
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    response = line_bot_api.get_message_content(image_message_id)
    file_content = response.content
   
    file_name = f"{image_message_id}.jpg"

    # Instantiate and use our unit-tested service
    gdrive_service = GoogleDriveService()
    folder_id = gdrive_service.find_or_create_folder(group)
    uploaded_file_id = gdrive_service.upload_file(
        file_name=file_name,
        file_content=file_content,
        folder_id=folder_id
    )

    # The function now returns the ID of the uploaded file
    return uploaded_file_id