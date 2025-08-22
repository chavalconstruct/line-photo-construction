"""
This module contains the logic for processing webhook events from the LINE API.
"""
import os
import aiohttp 
from src.google_drive_uploader import GoogleDriveService
from src.image_classifier import ImageClassifier
from linebot.v3.webhooks import ImageMessageContent
from linebot.v3.messaging import AsyncMessagingApi 
import logging

logger = logging.getLogger(__name__)

async def process_webhook_event(event, line_user_map, user_configs, line_bot_api: AsyncMessagingApi, channel_access_token: str):
    """
    Processes a single event from a LINE webhook payload.
    """
    if not isinstance(event.message, ImageMessageContent):
        return None
        
    line_user_id = event.source.user_id
    if not line_user_id:
        return None
    app_user = line_user_map.get(line_user_id)
    if not app_user:
        logger.warning(f"User ID {line_user_id} not found in map.")
        return None
        
    classifier = ImageClassifier(user_configs)
    file_data_for_classification = {'user': app_user}
    group = classifier.get_group_folder(file_data_for_classification)

    if not group:
        logger.warning(f"No group found for user {app_user}.")
        return None
        
    image_message_id = event.message.id

    # --- START: REFACTORED to use aiohttp (from test_download) ---
    file_content = None
    headers = {"Authorization": f"Bearer {channel_access_token}"}
    image_url = f"https://api-data.line.me/v2/bot/message/{image_message_id}/content"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, headers=headers) as resp:
                if resp.status == 200:
                    file_content = await resp.read()
                    logger.info(f"✅ Image content fetched successfully for message ID: {image_message_id}")
                else:
                    logger.error(f"❌ Failed to fetch image content. Status: {resp.status}, Response: {await resp.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching image content using aiohttp: {e}")
        return None
    # --- END: REFACTORED ---

    if not file_content:
        return None

    file_name = f"{image_message_id}.jpg"
    gdrive_service = GoogleDriveService()
    
    folder_id = gdrive_service.find_or_create_folder(group)
    uploaded_file_id = gdrive_service.upload_file(
        file_name=file_name,
        file_content=file_content,
        folder_id=folder_id
    )
    
    return uploaded_file_id