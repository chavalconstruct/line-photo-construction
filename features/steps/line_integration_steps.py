from behave import *
import json
from src.webhook_processor import process_webhook_event
from features.steps.classification_steps import step_impl as a_folder_should_be_created_step

@given('the LINE user ID "{line_user_id}" is mapped to the application user "{app_user}"')
def step_impl(context, line_user_id, app_user):
    """
    Stores a mapping between a LINE user ID and an internal application username.
    """
    if not hasattr(context, 'line_user_map'):
        context.line_user_map = {}
    context.line_user_map[line_user_id] = app_user

@when('the system receives a LINE webhook for an image message from user "{line_user_id}"')
def step_impl(context, line_user_id):
    """
    Simulates receiving a webhook and calls the real processing function.
    """
    mock_webhook_body = f"""
    {{
        "events": [
            {{
                "type": "message",
                "message": {{ "type": "image", "id": "msg_id_9876" }},
                "source": {{ "type": "user", "userId": "{line_user_id}" }}
            }}
        ]
    }}
    """
    webhook_data = json.loads(mock_webhook_body)
    first_event = webhook_data["events"][0]
    
    # Call our new, unit-tested function
    # We pass in the maps that were set up in the @given steps
    processing_result = process_webhook_event(
        event=first_event,
        line_user_map=context.line_user_map,
        user_configs=context.user_configs
    )
    
    # Store the result for the @then steps to check
    context.processing_result = processing_result


@then('the system should identify the user as "{app_user}"')
def step_impl(context, app_user):
    """
    Checks if the user was correctly identified by our processor.
    """
    # Assert against the actual result from our function
    assert context.processing_result is not None, "Processing result should not be None"
    identified_user = context.processing_result.get('app_user')
    assert identified_user == app_user, f"Expected user '{app_user}', but identified '{identified_user}'"

@then('the image content should be queued for upload to "{group_name}"')
def step_impl(context, group_name):
    """
    Checks if the identified image and user group are prepared for the next stage.
    """
    # Remove 'assert False' and check the result
    identified_group = context.processing_result.get('group')
    assert identified_group == group_name, f"Expected group '{group_name}', but found '{identified_group}'"