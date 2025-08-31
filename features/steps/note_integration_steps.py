from behave import *
from unittest.mock import call
import time
from linebot.v3.webhooks import TextMessageContent
from steps.line_integration_steps import create_mock_event, process_current_event


@when('user "{user_id}" sends another text message with "{text}"')
def step_impl(context, user_id, text):
    text_message = TextMessageContent(id=f"text_note_another_{time.time()}", text=text, quote_token="q_token_note_2")
    context.current_event = create_mock_event(user_id, text_message)
    process_current_event(context)

# --- THEN STEPS ---

@then('the note "{note_text}" should be saved to the "{group_name}" folder')
def step_impl(context, note_text, group_name):
    today_str = context.mocked_date.strftime("%Y-%m-%d")
    expected_log_filename = f"{today_str}_notes.txt"
    
    context.mock_gdrive_service.append_text_to_file.assert_any_call(
        expected_log_filename,
        note_text,
        "group_folder_id_1"
    )

@then('the note "{note_text}" should also be saved to the "{group_name}" folder')
def step_impl(context, note_text, group_name):
    context.execute_steps(f'Then the note "{note_text}" should be saved to the "{group_name}" folder')
    assert context.mock_gdrive_service.append_text_to_file.call_count == 2


@then('no notes should be saved')
def step_impl(context):
    context.mock_gdrive_service.append_text_to_file.assert_not_called()