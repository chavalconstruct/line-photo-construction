"""
This module contains the logic for processing webhook events from the LINE API.
"""
import logging
import aiohttp
from typing import Optional
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.messaging import AsyncMessagingApi
from src.state_manager import StateManager
from src.config_manager import ConfigManager
from src.google_drive_uploader import GoogleDriveService

logger = logging.getLogger(__name__)

async def download_image_content(image_message_id: str, channel_access_token: str) -> Optional[bytes]:
    """Downloads image content from LINE's content endpoint."""
    headers = {"Authorization": f"Bearer {channel_access_token}"}
    image_url = f"https://api-data.line.me/v2/bot/message/{image_message_id}/content"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, headers=headers) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Image content fetched for message ID: {image_message_id}")
                    return await resp.read()
                else:
                    logger.error(f"❌ Failed to fetch image. Status: {resp.status}, Response: {await resp.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching image content: {e}")
        return None

async def process_webhook_event(
    event: MessageEvent,
    state_manager: StateManager,
    config_manager: ConfigManager,
    line_bot_api: AsyncMessagingApi, # Kept for potential future use (e.g., reply messages)
    channel_access_token: str,
    parent_folder_id: Optional[str]
):
    """
    Processes a single event from a LINE webhook payload with stateful logic.
    """
    if not event.source or not event.source.user_id:
        logger.warning("Event has no source or user ID.")
        return

    user_id = event.source.user_id

    # --- Logic for Text Messages (Handling Secret Codes) ---
    if isinstance(event.message, TextMessageContent):
        secret_code = event.message.text
        group = config_manager.get_group_from_secret_code(secret_code)
        if group:
            state_manager.set_pending_upload(user_id, group)
            logger.info(f"State set for user {user_id} to upload to {group}.")
        else:
            logger.info(f"Received non-code text from {user_id}. Ignoring.")

    # --- Logic for Image Messages (Handling Uploads) ---
    elif isinstance(event.message, ImageMessageContent):
        logger.info(f"Image received from {user_id}. Checking for pending state.")
        pending_group = state_manager.consume_pending_upload(user_id)

        if pending_group:
            logger.info(f"User {user_id} is in a pending state for group '{pending_group}'. Proceeding with upload.")
            image_content = await download_image_content(event.message.id, channel_access_token)

            if image_content:
                gdrive_service = GoogleDriveService()
                folder_id = gdrive_service.find_or_create_folder(pending_group, parent_folder_id=parent_folder_id)
                file_name = f"{event.message.id}.jpg"
                gdrive_service.upload_file(
                    file_name=file_name,
                    file_content=image_content,
                    folder_id=folder_id
                )
                logger.info(f"Successfully uploaded {file_name} for user {user_id}.")
            else:
                 logger.error(f"Could not download image for user {user_id}, upload aborted.")
        else:
            logger.warning(f"User {user_id} sent an image but was not in a pending state. Ignoring.")