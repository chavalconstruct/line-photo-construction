import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict

from linebot.v3.webhooks import MessageEvent
from src.state_manager import StateManager
from src.google_drive_uploader import GoogleDriveService

logger = logging.getLogger(__name__)

async def download_image_content(image_message_id: str, channel_access_token: str) -> Optional[bytes]:
    """Downloads image content from LINE's content endpoint with retry logic."""
    headers: Dict[str, str] = {"Authorization": f"Bearer {channel_access_token}"}
    image_url: str = f"https://api-data.line.me/v2/bot/message/{image_message_id}/content"
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.get(image_url, headers=headers) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    else:
                        logger.error(f"❌ Failed to fetch image. Status: {resp.status}, Response: {await resp.text()}")
                        return None 
            except aiohttp.ClientError as e:
                logger.warning(f"⚠️ Attempt {attempt + 1}/3 failed to download image due to a connection error: {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"An unexpected error occurred while fetching image content: {e}")
                return None
            
    logger.error(f"❌ Failed to download image after 3 attempts for message ID {image_message_id}.")
    return None

async def handle_image_message(
    event: MessageEvent,
    state_manager: StateManager,
    gdrive_service: GoogleDriveService,
    channel_access_token: str,
    parent_folder_id: Optional[str]
) -> None:
    """
    Handles all logic for incoming image message events.
    """
    if not event.source or not event.source.user_id:
        return

    user_id: str = event.source.user_id
    active_group: Optional[str] = state_manager.get_active_group(user_id)
    
    if active_group:
        logger.info(f"Image received from user {user_id} with active session for group '{active_group}'.")
        
        image_content: Optional[bytes] = await download_image_content(event.message.id, channel_access_token)
        
        if image_content:            
            group_folder_id: str = gdrive_service.find_or_create_folder(active_group, parent_folder_id=parent_folder_id)
            today_str: str = datetime.now().strftime("%Y-%m-%d")
            daily_folder_id: str = gdrive_service.find_or_create_folder(today_str, parent_folder_id=group_folder_id)

            file_name: str = f"{event.message.id}.jpg"
            gdrive_service.upload_file(file_name, image_content, daily_folder_id)
            
    else:
        logger.warning(f"Image received from user {user_id} but they have no active session. Ignoring.")