import logging
from datetime import datetime
from typing import Optional, Dict, Any

from linebot.v3.webhooks import MessageEvent
from linebot.v3.messaging import (
    AsyncMessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

from src.state_manager import StateManager
from src.config_manager import ConfigManager
from src.google_drive_uploader import GoogleDriveService
from src.command_parser import parse_command

logger = logging.getLogger(__name__)
CONFIG_FILE: str = "config.json"

async def _handle_command(
    command: Dict[str, str],
    user_id: str,
    config_manager: ConfigManager,
    line_bot_api: AsyncMessagingApi,
    event: MessageEvent,
) -> None:
    """Handles administrative commands."""
    action: Optional[str] = command.get("action")
    reply_text: str = ""

    if action == "list":
        all_codes: Dict[str, str] = config_manager.get_all_secret_codes()
        if not all_codes:
            reply_text = "No secret codes are currently configured."
        else:
            header: str = "รายชื่อไซต์ก่อสร้าง:\n"
            lines: List[str] = [f"{code}  {group}" for code, group in all_codes.items()]
            reply_text = header + "\n".join(lines)
        logger.info(f"User {user_id} listed all codes.")
    
    elif action in ["add", "remove"]:
        if not config_manager.is_admin(user_id):
            reply_text = "Error: You do not have permission to use this command."
            logger.warning(
                f"Non-admin user {user_id} attempted to use command '{action}'."
            )
        elif action == "add":
            code: str = command["code"]
            group: str = command["group"]
            config_manager.add_secret_code(code, group)
            config_manager.save_config(CONFIG_FILE)
            reply_text = f"Success: Code {code} has been added for group {group}."
            logger.info(f"Admin {user_id} added code {code} for group {group}.")
        elif action == "remove":
            code = command["code"]
            was_removed: bool = config_manager.remove_secret_code(code)
            if was_removed:
                config_manager.save_config(CONFIG_FILE)
                reply_text = f"Success: Code {code} has been removed."
                logger.info(f"Admin {user_id} removed code {code}.")
            else:
                reply_text = (
                    f"Error: Code {code} was not found and could not be removed."
                )
                logger.warning(
                    f"Admin {user_id} tried to remove non-existent code {code}."
                )
    else:
        reply_text = "Error: Unknown command."
        logger.error(f"Unknown command action '{action}' from user {user_id}.")

    await line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token, messages=[TextMessage(text=reply_text)]
        )
    )

async def handle_text_message(
    event: MessageEvent,
    state_manager: StateManager,
    config_manager: ConfigManager,
    gdrive_service: GoogleDriveService,
    line_bot_api: AsyncMessagingApi,
    parent_folder_id: Optional[str],
) -> None:
    """Orchestrates responses to incoming text messages.

    This function acts as the primary router for text messages. It first
    checks if the message is an administrative command. If not, it processes
    the message for session management (starting a new session with a secret
code)
    or for saving content as a note if a session is already active.

    Args:
        event: The MessageEvent object from the LINE webhook.
        state_manager: The manager for user sessions.
        config_manager: The manager for application configuration and secrets.
        gdrive_service: The service for interacting with Google Drive.
        line_bot_api: The LINE Messaging API client.
        parent_folder_id: The ID of the root folder in Google Drive, if configured.
    """
    if not event.source or not event.source.user_id:
        return

    user_id: str = event.source.user_id
    text: str = event.message.text
    command: Optional[Dict[str, str]] = parse_command(text)

    if command:
        await _handle_command(command, user_id, config_manager, line_bot_api, event)
        return

    note_to_save: Optional[str] = None
    active_group: Optional[str] = None
    group_from_code: Optional[str] = None

    all_codes: Dict[str, str] = config_manager.get_all_secret_codes()
    for code, group in all_codes.items():
        if text.startswith(code):
            group_from_code = group
            state_manager.set_pending_upload(user_id, group_from_code)
            active_group = group_from_code

            note: str = text[len(code) :].lstrip()
            if note:
                note_to_save = note

            logger.info(
                f"Session started/refreshed for user {user_id} to group '{active_group}'."
            )
            break

    if not group_from_code:
        active_group = state_manager.get_active_group(user_id)
        if active_group:
            note_to_save = text

    if active_group and note_to_save:
        logger.info(f"Saving note for user {user_id} in group '{active_group}'.")
        today_str: str = datetime.now().strftime("%Y-%m-%d")
        daily_log_filename: str = f"{today_str}_notes.txt"

        group_folder_id: str = gdrive_service.find_or_create_folder(
            active_group, parent_folder_id
        )
        daily_folder_id: str = gdrive_service.find_or_create_folder(
            today_str, parent_folder_id=group_folder_id
        )

        gdrive_service.append_text_to_file(
            daily_log_filename, note_to_save, daily_folder_id
        )
        