from behave import *
from src.config_manager import ConfigManager
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent,
    UserSource, DeliveryContext, ContentProvider
)
from unittest.mock import AsyncMock, patch
import time

def create_mock_event(user_id, message_content):
    return MessageEvent(
        source=UserSource(user_id=user_id), message=message_content,
        timestamp=1673377200000, mode="active", webhook_event_id="w_event_id",
        delivery_context=DeliveryContext(is_redelivery=False)
    )

@given('the secret code "{secret_code}" is configured for the "{group_name}" folder')
def step_impl(context, secret_code, group_name):
    if not hasattr(context, 'config_data'):
        context.config_data = {"secret_code_map": {}, "line_user_map": {}}
    context.config_data["secret_code_map"][secret_code] = group_name

@given('the system is ready to process events for user "{app_user}" with LINE ID "{user_id}"')
def step_impl(context, app_user, user_id):
    if not hasattr(context, 'config_data'):
        context.config_data = {"secret_code_map": {}, "line_user_map": {}}
    context.config_data["line_user_map"][user_id] = app_user

def _user_sends_image(context, app_user, image_id="img_msg_1"):
    """Helper to simulate a user sending an image."""
    user_id = next(key for key, value in context.config_data["line_user_map"].items() if value == app_user)
    image_message = ImageMessageContent(id=image_id, quote_token="q_token", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    context.execute_steps('When the system processes the current event')

@when('user "{app_user}" sends a text message with "{secret_code}"')
def step_impl(context, app_user, secret_code):
    user_id = next(key for key, value in context.config_data["line_user_map"].items() if value == app_user)
    text_message = TextMessageContent(id="text_msg_1", text=secret_code, quote_token="q_token")
    context.current_event = create_mock_event(user_id, text_message)
    context.execute_steps('When the system processes the current event')

@when('user "{app_user}" sends an image')
def step_impl(context, app_user):
    _user_sends_image(context, app_user, image_id="img_msg_1")

# --- NEW STEPS FOR MULTI-IMAGE SESSION ---

@when('user "{app_user}" sends another image')
def step_impl(context, app_user):
    _user_sends_image(context, app_user, image_id="img_msg_2")

@when('the session for user "{app_user}" expires')
def step_impl(context, app_user):
    # We simulate time passing by patching time.time()
    # In a real test, StateManager's session duration would be short
    user_id = next(key for key, value in context.config_data["line_user_map"].items() if value == app_user)
    
    # Get the session start time and patch time.time() to return a future time
    session_start_time = context.state_manager._pending_uploads[user_id]['timestamp']
    future_time = session_start_time + context.state_manager.SESSION_DURATION_SECONDS + 1
    
    # We use a patch to fast-forward time
    with patch('time.time', return_value=future_time):
        context.execute_steps(f'When user "{app_user}" sends an image')

# ---------------------------------------------

@when('the system processes the current event')
def step_impl(context):
    config_manager = ConfigManager(context.config_data)

    from src.webhook_processor import process_webhook_event
    import asyncio
    
    # We are now testing session expiration, so let's use a short duration
    context.state_manager.SESSION_DURATION_SECONDS = 10 
    
    asyncio.run(process_webhook_event(
        event=context.current_event,
        state_manager=context.state_manager,
        config_manager=config_manager,
        line_bot_api=AsyncMock(),
        channel_access_token="dummy_token",
        parent_folder_id=None
    ))

@then('the image from "{app_user}" should be uploaded to the "{group_name}" folder')
def step_impl(context, app_user, group_name):
    context.mock_gdrive_service.find_or_create_folder.assert_called_with(group_name, parent_folder_id=None)
    # Check that upload_file was called AT LEAST once.
    context.mock_gdrive_service.upload_file.assert_called()

# --- NEW STEPS FOR MULTI-IMAGE SESSION ---

@then('the second image from "{app_user}" should also be uploaded to the "{group_name}" folder')
def step_impl(context, app_user, group_name):
    # Verify the folder was targeted correctly again
    context.mock_gdrive_service.find_or_create_folder.assert_called_with(group_name, parent_folder_id=None)
    # Check that upload was called twice in total
    assert context.mock_gdrive_service.upload_file.call_count == 2

# ---------------------------------------------

@then('no files should be uploaded')
def step_impl(context):
    context.mock_gdrive_service.upload_file.assert_not_called()