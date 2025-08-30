from behave import *
from src.config_manager import ConfigManager
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent,
    UserSource, DeliveryContext, ContentProvider
)
from unittest.mock import AsyncMock, patch, call
import time
import asyncio

# Helper to create a mock event, ensures unique event IDs
def create_mock_event(user_id, message_content):
    event_id = f"w_event_{time.time()}"
    return MessageEvent(
        source=UserSource(user_id=user_id), message=message_content,
        timestamp=int(time.time() * 1000), mode="active", webhook_event_id=event_id,
        delivery_context=DeliveryContext(is_redelivery=False)
    )

# Helper to process the event currently stored in the context
def process_current_event(context):
    config_manager = ConfigManager(context.config_data)
    from src.webhook_processor import process_webhook_event

    asyncio.run(process_webhook_event(
        event=context.current_event,
        state_manager=context.state_manager,
        config_manager=config_manager,
        line_bot_api=AsyncMock(),
        channel_access_token="dummy_token",
        parent_folder_id="dummy_parent_id"
    ))
    # Stop any time patcher immediately after use
    if hasattr(context, 'time_patcher') and context.time_patcher:
        context.time_patcher.stop()
        context.time_patcher = None

@given('the secret code "{secret_code}" is configured for the "{group_name}" folder')
def step_impl(context, secret_code, group_name):
    if not hasattr(context, 'config_data'):
        context.config_data = {"secret_code_map": {}}
    context.config_data["secret_code_map"][secret_code] = group_name

# --- UNAMBIGUOUS 'WHEN' STEPS ---

@when('user "{user_id}" sends a text message with "{secret_code}"')
def step_impl(context, user_id, secret_code):
    text_message = TextMessageContent(id=f"text_{time.time()}", text=secret_code, quote_token="q_token")
    context.current_event = create_mock_event(user_id, text_message)
    process_current_event(context)

@when('user "{user_id}" sends an image')
def step_impl(context, user_id):
    image_message = ImageMessageContent(id=f"image_{user_id}_{time.time()}", quote_token="q_token", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    process_current_event(context)

@when('another user "{user_id}" sends an image')
def step_impl(context, user_id):
    image_message = ImageMessageContent(id=f"image_another_{user_id}_{time.time()}", quote_token="q_token_intruder", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    process_current_event(context)

@when('user "{user_id}" sends another image')
def step_impl(context, user_id):
    image_message = ImageMessageContent(id=f"image_another_{user_id}_{time.time()}", quote_token="q_token_multi", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    process_current_event(context)

@when('the session for user "{user_id}" expires')
def step_impl(context, user_id):
    session_start_time = context.state_manager._pending_uploads[user_id]['timestamp']
    future_time = session_start_time + context.state_manager.SESSION_DURATION_SECONDS + 1
    
    context.time_patcher = patch('time.time', return_value=future_time)
    context.time_patcher.start()

# --- UPDATED 'THEN' STEPS ---

@then('the image from user "{user_id}" should be uploaded to the "{group_name}" folder')
def step_impl(context, user_id, group_name):
    today_str = context.mocked_date.strftime("%Y-%m-%d")
    
    # We check that the GDrive service was called to create the main folder and then the daily subfolder.
    # The `side_effect` in environment.py returns 'group_folder_id_1' on the first call.
    expected_calls = [
        call(group_name, parent_folder_id="dummy_parent_id"),
        call(today_str, parent_folder_id="group_folder_id_1")
    ]
    context.mock_gdrive_service.find_or_create_folder.assert_has_calls(expected_calls)
    context.mock_gdrive_service.upload_file.assert_called()

@then('the second image from user "{user_id}" should also be uploaded to the "{group_name}" folder')
def step_impl(context, user_id, group_name):
    # Check that upload was called twice in total
    assert context.mock_gdrive_service.upload_file.call_count == 2, \
        f"Expected 2 uploads, but found {context.mock_gdrive_service.upload_file.call_count}"

@then('no files should be uploaded')
def step_impl(context):
    context.mock_gdrive_service.upload_file.assert_not_called()

@then('the interrupting image from "{user_id}" was not uploaded')
def step_impl(context, user_id):
    # Check the number of uploads at this specific point in the scenario
    assert context.mock_gdrive_service.upload_file.call_count == 0, \
        "An interrupting image was uploaded, but it should have been ignored."