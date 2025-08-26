from behave import *
from src.config_manager import ConfigManager
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent, ImageMessageContent,
    UserSource, DeliveryContext, ContentProvider
)
from unittest.mock import AsyncMock

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

def _user_sends_image(context, app_user):
    user_id = next(key for key, value in context.config_data["line_user_map"].items() if value == app_user)
    image_message = ImageMessageContent(id="img_msg_1", quote_token="q_token", content_provider=ContentProvider(type="line"))
    context.current_event = create_mock_event(user_id, image_message)
    context.execute_steps('When the system processes the current event')

@when('user "{app_user}" sends a text message with "{secret_code}"')
def step_impl(context, app_user, secret_code):
    user_id = next(key for key, value in context.config_data["line_user_map"].items() if value == app_user)
    text_message = TextMessageContent(id="text_msg_1", text=secret_code, quote_token="q_token")
    context.current_event = create_mock_event(user_id, text_message)
    context.execute_steps('When the system processes the current event')

@when('user "{app_user}" sends an image')
@then('user "{app_user}" sends an image')
def step_impl(context, app_user):
    _user_sends_image(context, app_user)

@when('the system processes the current event')
def step_impl(context):
    # The 'with patch' is gone! We now use mocks from the context.
    config_manager = ConfigManager(context.config_data)

    from src.webhook_processor import process_webhook_event
    import asyncio
    asyncio.run(process_webhook_event(
        event=context.current_event,
        state_manager=context.state_manager, # <-- Use the persistent manager
        config_manager=config_manager,
        line_bot_api=AsyncMock(),
        channel_access_token="dummy_token",
        parent_folder_id=None
    ))

@then('the image from "{app_user}" should be uploaded to the "{group_name}" folder')
def step_impl(context, app_user, group_name):
    # Now this assertion will check the mock that has seen all events
    context.mock_gdrive_service.find_or_create_folder.assert_called_with(group_name, parent_folder_id=None)
    context.mock_gdrive_service.upload_file.assert_called_once()

@then('no files should be uploaded')
def step_impl(context):
    context.mock_gdrive_service.upload_file.assert_not_called()