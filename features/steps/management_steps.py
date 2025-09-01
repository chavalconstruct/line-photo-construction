import json
from behave import *
from unittest.mock import AsyncMock, patch, MagicMock
import copy 
from linebot.v3.webhooks import TextMessageContent
from tests.test_webhook_processor import create_mock_event

CONFIG_FILE_PATH = "config.json"

def user_sends_message(context, user_id, message_text):
    """A helper function to simulate a user sending a text message."""
    from src.webhook_processor import process_webhook_event
    from src.config_manager import ConfigManager
    import asyncio
    mock_gdrive_service = MagicMock()

    # We need to reload the config data for each event to get the latest state
    with open(CONFIG_FILE_PATH, 'r') as f:
        config_data = json.load(f)
    
    # Mock the LINE API to capture reply messages
    mock_line_api = AsyncMock()
    mock_line_api.reply_message = AsyncMock()
    context.mock_line_api = mock_line_api # Save for 'Then' step

    text_message = TextMessageContent(id="bdd_msg", text=message_text, quote_token="bdd_q_token")
    event = create_mock_event(user_id, text_message, reply_token="bdd_reply_token")

    # --- THIS IS THE FIX ---
    # We pass a DEEP COPY of the config data to the manager.
    # This prevents the manager from accidentally modifying the original
    # dictionary in memory, ensuring true test isolation.
    isolated_config_manager = ConfigManager(copy.deepcopy(config_data))
    # ---------------------

    # Run the actual event processor
    asyncio.run(process_webhook_event(
        event=event,
        state_manager=context.state_manager,
        config_manager=isolated_config_manager,
        gdrive_service=mock_gdrive_service,
        line_bot_api=mock_line_api,
        channel_access_token="dummy_token",
        parent_folder_id=None
    ))

# --- Given Steps ---

@given('the system is configured with "{user_id}" as an admin user')
def step_impl(context, user_id):
    # This step assumes the config.json is already set up correctly by the user.
    # We can add a check here for clarity if needed.
    with open(CONFIG_FILE_PATH, 'r') as f:
        config_data = json.load(f)
    assert user_id in config_data.get("admins", []), f"User {user_id} not found in admins list in config.json"
    # Store the user_id for later use in 'When' steps
    context.admin_user_id = user_id

@given('the system is configured with "{user_id}" as a non-admin user')
def step_impl(context, user_id):
    with open(CONFIG_FILE_PATH, 'r') as f:
        config_data = json.load(f)
    assert user_id not in config_data.get("admins", []), f"User {user_id} was found in admins list, but should not be."
    context.non_admin_user_id = user_id


# --- When Steps ---

@when('admin user "{user_id}" sends the message "{message_text}"')
def step_impl(context, user_id, message_text):
    user_sends_message(context, user_id, message_text)

@when('non-admin user "{user_id}" sends the message "{message_text}"')
def step_impl(context, user_id, message_text):
    user_sends_message(context, user_id, message_text)


# --- Then Steps ---

@then('the bot should reply with "{expected_reply}"')
def step_impl(context, expected_reply):
    # Check that our mock API was called to send a reply
    context.mock_line_api.reply_message.assert_called_once()
    
    # Extract the text from the arguments it was called with
    reply_request = context.mock_line_api.reply_message.call_args[0][0]
    actual_reply_text = reply_request.messages[0].text
    assert actual_reply_text == expected_reply, f"Expected reply '{expected_reply}', but got '{actual_reply_text}'"

@then('the bot should reply with a list of all secret codes')
def step_impl(context):
    """
    Checks that the bot sent a reply and that the reply contains
    the expected format and content for a list of codes.
    """
    # 1. Check that a reply was sent
    context.mock_line_api.reply_message.assert_called_once()
    
    # 2. Extract the actual reply text
    reply_request = context.mock_line_api.reply_message.call_args[0][0]
    actual_reply_text = reply_request.messages[0].text

    # 3. Verify the content of the reply
    # We check for key parts instead of the exact string to make the test more robust.
    assert "รายชื่อไซต์ก่อสร้าง:" in actual_reply_text
    
    # Check for at least one known code from our test config to ensure it's listing them.
    # From config.json.template
    assert "#s1  Group_A_Photos" in actual_reply_text
    assert "#s2  Group_B_Photos" in actual_reply_text

@then('the secret code "{code}" should now be mapped to the group "{group}"')
def step_impl(context, code, group):
    with open(CONFIG_FILE_PATH, 'r') as f:
        config_data = json.load(f)
    assert config_data["secret_code_map"].get(code) == group, f"Code {code} is not mapped to {group} in config.json"

@then('the secret code "{code}" should no longer exist in the configuration')
def step_impl(context, code):
    with open(CONFIG_FILE_PATH, 'r') as f:
        config_data = json.load(f)
    assert code not in config_data["secret_code_map"], f"Code {code} was found in config.json but should have been removed."

@then('the secret code "{code}" should still be mapped to the group "{group}"')
def step_impl(context, code, group):
    # This is effectively the same as checking if it's mapped
    context.execute_steps(f'Then the secret code "{code}" should now be mapped to the group "{group}"')