"""
This module acts as a router for incoming webhook events from the LINE API,
directing them to the appropriate handlers based on message type.
"""
import logging
from typing import Optional, Any

import redis
import os

from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.messaging import AsyncMessagingApi

from src.state_manager import StateManager
from src.config_manager import ConfigManager
from src.google_drive_uploader import GoogleDriveService

# Import handlers
from src.handlers.text_message_handler import handle_text_message
from src.handlers.image_message_handler import handle_image_message


logger = logging.getLogger(__name__)

# --- Redis Client Initialization ---
redis_client: Optional[redis.Redis] = None
redis_url: Optional[str] = os.getenv('REDIS_URL')
if redis_url:
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Successfully connected to Redis.")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        redis_client = None
else:
    logger.warning("REDIS_URL not found. Redis client is not initialized.")


async def process_webhook_event(
    event: MessageEvent,
    state_manager: StateManager,
    config_manager: ConfigManager,
    gdrive_service: GoogleDriveService,
    line_bot_api: AsyncMessagingApi,
    channel_access_token: str,
    parent_folder_id: Optional[str]
) -> None:
    """
    Acts as a router, checking for duplicate events and then passing the
    event to the appropriate handler based on its message type.
    """
    if not isinstance(event, MessageEvent):
        logger.info(f"Received non-message event: {type(event).__name__}. Ignoring.")
        return

    # --- Duplicate Event Check (using Redis) ---
    if redis_client:
        message_id: str = event.message.id
        redis_key: str = f"line_msg_{message_id}"
        if not redis_client.set(redis_key, "processed", nx=True, ex=60):
            logger.warning(f"⚠️ Duplicate event received: message_id={message_id}. Ignoring.")
            return

    # --- Routing Logic ---
    if isinstance(event.message, TextMessageContent):
        await handle_text_message(
            event,
            state_manager,
            config_manager,
            gdrive_service,
            line_bot_api,
            parent_folder_id
        )
    elif isinstance(event.message, ImageMessageContent):
        await handle_image_message(
            event,
            state_manager,
            gdrive_service,
            channel_access_token,
            parent_folder_id
        )