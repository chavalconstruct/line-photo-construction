from behave import *
from src.config_manager import ConfigManager
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent,
    UserSource, DeliveryContext, ContentProvider
)
from unittest.mock import AsyncMock, patch
import time

# create_mock_event remains the same
def create_mock_event(user_id, message_content):
    return MessageEvent(
        source=UserSource(user_id=user_id), message=message_content,
        timestamp=1673377200000, mode="active", webhook_event_id="w_event_id",
        delivery_context=DeliveryContext(is_redelivery=False)
    )

@given('the secret code "{secret_code}" is configured for the "{group_name}" folder')
def step_impl(context, secret_code, group_name):
    # We now only need the secret code map
    if not hasattr(context, 'config_data'):
        context.config_data = {"secret_code_map": {}}
    context.config_data["secret_code_map"][secret_code] = group_name

# REMOVED: The step for setting up a user with a LINE ID, as it's no longer needed.

# --- WHEN STEPS: Refactored to use user_id directly ---

@when('user "{user_id}" sends a text message with "{secret_code}"')
def step_impl(context, user_id, secret_code):
    text_message = TextMessageContent(id="text_msg_1", text=secret_code, quote_token="q_token")
    context.current_event = create_mock_event(user_id, text_message)
    context.execute_steps('When the system processes the current event')

@when('user "{user_id}" sends an image')
def step_impl(context, user_id):
    # Use a unique ID for each image sent to be safe
    image_id = f"image_for_{user_id}_{time.time()}" 
    image_message = ImageMessageContent(id=image_id, quote_token="q_token", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    context.execute_steps('When the system processes the current event')

# Let's make the "another user" step more explicit instead of calling another step
@when('another user "{user_id}" sends an image')
def step_impl(context, user_id):
    image_id = f"image_for_{user_id}_{time.time()}"
    image_message = ImageMessageContent(id=image_id, quote_token="q_token_intruder", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    context.execute_steps('When the system processes the current event')

@when('user "{user_id}" sends an image again')
def step_impl(context, user_id):
    # This step simulates the original user sending another image
    image_message = ImageMessageContent(id="img_msg_2", quote_token="q_token", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    context.execute_steps('When the system processes the current event')

# Combine the "sends again" and "sends another" steps into one
@when('user "{user_id}" sends another image')
def step_impl(context, user_id):
    image_id = f"image_for_{user_id}_{time.time()}"
    image_message = ImageMessageContent(id=image_id, quote_token="q_token_multi", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    context.execute_steps('When the system processes the current event')

@when('the session for user "{user_id}" expires')
def step_impl(context, user_id):
    # We now START the patcher here and keep it running.
    session_start_time = context.state_manager._pending_uploads[user_id]['timestamp']
    future_time = session_start_time + context.state_manager.SESSION_DURATION_SECONDS + 1
    
    context.time_patcher = patch('time.time', return_value=future_time)
    context.time_patcher.start()

@when('the system processes the current event')
def step_impl(context):
    # This step remains largely the same
    config_manager = ConfigManager(context.config_data)
    from src.webhook_processor import process_webhook_event
    import asyncio
    
    # Use a short session duration for testing expiration
    context.state_manager.SESSION_DURATION_SECONDS = 10 
    
    asyncio.run(process_webhook_event(
        event=context.current_event,
        state_manager=context.state_manager,
        config_manager=config_manager,
        line_bot_api=AsyncMock(),
        channel_access_token="dummy_token",
        parent_folder_id=None
    ))

    # After the event is processed, we stop the time patcher if it's active.
    if hasattr(context, 'time_patcher') and context.time_patcher:
        context.time_patcher.stop()
        context.time_patcher = None

@then('the image from user "{user_id}" should be uploaded to the "{group_name}" folder')
def step_impl(context, user_id, group_name):
    context.mock_gdrive_service.find_or_create_folder.assert_called_with(group_name, parent_folder_id=None)
    # Check that upload_file was called AT LEAST once.
    context.mock_gdrive_service.upload_file.assert_called()

@then('the second image from user "{user_id}" should also be uploaded to the "{group_name}" folder')
def step_impl(context, user_id, group_name):
    context.mock_gdrive_service.find_or_create_folder.assert_called_with(group_name, parent_folder_id=None)
    # Check that upload was called twice in total
    assert context.mock_gdrive_service.upload_file.call_count == 2

@then('no files should be uploaded')
def step_impl(context):
    context.mock_gdrive_service.upload_file.assert_not_called()