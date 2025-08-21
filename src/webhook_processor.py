"""
This module contains the logic for processing webhook events from the LINE API.
"""
import os
from linebot import LineBotApi
from src.google_drive_uploader import GoogleDriveService
# --- ADDED IMPORT ---
from src.image_classifier import ImageClassifier

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "dummy_token")

def process_webhook_event(event, line_user_map, user_configs):
    """
    Processes a single event from a LINE webhook payload.
    """
    if event.get("message", {}).get("type") != "image":
        return None
    line_user_id = event.get("source", {}).get("userId")
    if not line_user_id:
        return None
    app_user = line_user_map.get(line_user_id)
    if not app_user:
        return None

    # --- REFACTORED LOGIC ---
    # REPLACED: group = user_configs.get(app_user)
    # WITH the new Classifier class to handle the logic.
    classifier = ImageClassifier(user_configs)
    file_data_for_classification = {'user': app_user}
    group = classifier.get_group_folder(file_data_for_classification)
    # --- END REFACTOR ---

    if not group:
        # If classifier returns None, we stop processing.
        return None
    image_message_id = event.get("message", {}).get("id")

    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    response = line_bot_api.get_message_content(image_message_id)
    file_content = response.content
    
    file_name = f"{image_message_id}.jpg"

    gdrive_service = GoogleDriveService()
    
    folder_id = gdrive_service.find_or_create_folder(group)

    uploaded_file_id = gdrive_service.upload_file(
        file_name=file_name,
        file_content=file_content,
        folder_id=folder_id
    )

    return uploaded_file_id