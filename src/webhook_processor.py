"""
This module contains the logic for processing webhook events from the LINE API.
"""
import logging
import aiohttp
from typing import Optional
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.messaging import AsyncMessagingApi, ReplyMessageRequest, TextMessage
from src.state_manager import StateManager
from src.config_manager import ConfigManager
from src.google_drive_uploader import GoogleDriveService
from src.command_parser import parse_command

logger = logging.getLogger(__name__)
CONFIG_FILE = "config.json"

async def download_image_content(image_message_id: str, channel_access_token: str) -> Optional[bytes]:
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

async def handle_admin_command(command: dict, user_id: str, config_manager: ConfigManager, line_bot_api: AsyncMessagingApi, event: MessageEvent):
    """Processes a parsed command dictionary."""
    if not config_manager.is_admin(user_id):
        reply_text = "Error: You do not have permission to use this command."
        logger.warning(f"Non-admin user {user_id} attempted to use a command.")
    else:
        action = command.get("action")
        if action == "add":
            code, group = command["code"], command["group"]
            config_manager.add_secret_code(code, group)
            config_manager.save_config(CONFIG_FILE)
            reply_text = f"Success: Code {code} has been added for group {group}."
            logger.info(f"Admin {user_id} added code {code} for group {group}.")
        elif action == "remove":
            code = command["code"]
            config_manager.remove_secret_code(code)
            config_manager.save_config(CONFIG_FILE)
            reply_text = f"Success: Code {code} has been removed."
            logger.info(f"Admin {user_id} removed code {code}.")
        else:
            reply_text = "Error: Unknown command."
            logger.error(f"Unknown command action '{action}' from admin {user_id}.")

    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_text)]
        )
    )

async def process_webhook_event(
    event: MessageEvent,
    state_manager: StateManager,
    config_manager: ConfigManager,
    line_bot_api: AsyncMessagingApi,
    channel_access_token: str,
    parent_folder_id: Optional[str]
):
    if not event.source or not event.source.user_id:
        logger.warning("Event has no source or user ID.")
        return

    user_id = event.source.user_id

    if isinstance(event.message, TextMessageContent):
        text = event.message.text
        
        command = parse_command(text)
        if command:
            await handle_admin_command(command, user_id, config_manager, line_bot_api, event)
            return

        group = config_manager.get_group_from_secret_code(text)
        if group:
            state_manager.set_pending_upload(user_id, group)
            logger.info(f"State set for user {user_id} to upload to {group}.")
        else:
            logger.info(f"Received non-code, non-command text from {user_id}. Ignoring.")

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
                gdrive_service.upload_file(file_name, image_content, folder_id)
                logger.info(f"Successfully uploaded {file_name} for user {user_id}.")
            else:
                 logger.error(f"Could not download image for user {user_id}, upload aborted.")
        else:
            logger.warning(f"User {user_id} sent an image but was not in a pending state. Ignoring.")