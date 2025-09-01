import logging
from datetime import datetime
from typing import Optional

from linebot.v3.webhooks import MessageEvent, TextMessageContent
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
CONFIG_FILE = "config.json"

async def _handle_command(
    command: dict,
    user_id: str,
    config_manager: ConfigManager,
    line_bot_api: AsyncMessagingApi,
    event: MessageEvent,
):
    """Handles administrative commands."""
    action = command.get("action")
    if action == "list":
        all_codes = config_manager.get_all_secret_codes()
        if not all_codes:
            reply_text = "No secret codes are currently configured."
        else:
            header = "รายชื่อไซต์ก่อสร้าง:\n"
            lines = [f"{code}  {group}" for code, group in all_codes.items()]
            reply_text = header + "\n".join(lines)
        logger.info(f"User {user_id} listed all codes.")
    elif action in ["add", "remove"]:
        if not config_manager.is_admin(user_id):
            reply_text = "Error: You do not have permission to use this command."
            logger.warning(
                f"Non-admin user {user_id} attempted to use command '{action}'."
            )
        elif action == "add":
            code, group = command["code"], command["group"]
            config_manager.add_secret_code(code, group)
            config_manager.save_config(CONFIG_FILE)
            reply_text = f"Success: Code {code} has been added for group {group}."
            logger.info(f"Admin {user_id} added code {code} for group {group}.")
        elif action == "remove":
            code = command["code"]
            was_removed = config_manager.remove_secret_code(code)
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
):
    """
    Handles all logic for incoming text message events, including commands,
    session management, and note-taking.
    """
    if not event.source or not event.source.user_id:
        return

    user_id = event.source.user_id
    text = event.message.text
    command = parse_command(text)

    if command:
        await _handle_command(command, user_id, config_manager, line_bot_api, event)
        return

    note_to_save = None
    active_group = None
    group_from_code = None

    # 1. More robustly check if the text starts with any known secret code.
    all_codes = config_manager.get_all_secret_codes()
    for code in all_codes:
        if text.startswith(code):
            group_from_code = all_codes[code]
            state_manager.set_pending_upload(user_id, group_from_code)
            active_group = group_from_code

            # Extract the note by removing the code prefix.
            note_to_save = text[len(code) :].lstrip()  # Use lstrip to remove leading space if it exists
            if not note_to_save:  # Handle case where only code is sent
                note_to_save = None

            logger.info(
                f"Session started/refreshed for user {user_id} to group '{active_group}'."
            )
            break  # Stop after finding the first match

    # 2. If no session was started, check for a pre-existing active session.
    if not group_from_code:
        active_group = state_manager.get_active_group(user_id)
        if active_group:
            note_to_save = text

    # 3. If we have an active group and a note to save, then save it.
    if active_group and note_to_save:
        logger.info(f"Saving note for user {user_id} in group '{active_group}'.")
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_log_filename = f"{today_str}_notes.txt"

        # 1. Find the main group folder
        group_folder_id = gdrive_service.find_or_create_folder(
            active_group, parent_folder_id
        )
        # 2. Find/create the daily subfolder inside the group folder
        daily_folder_id = gdrive_service.find_or_create_folder(
            today_str, parent_folder_id=group_folder_id
        )

        # 3. Append the note to the file inside the daily folder
        gdrive_service.append_text_to_file(
            daily_log_filename, note_to_save, daily_folder_id
        )

        # Keep the session alive after a successful action
        state_manager.refresh_session(user_id)