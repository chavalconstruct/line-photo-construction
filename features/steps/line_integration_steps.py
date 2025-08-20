from behave import *
import json

# We are using a step from another file, so we tell behave to look for it
# This avoids re-implementing the user group configuration step
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
    Simulates the system receiving a webhook payload from the LINE API.
    The payload is processed and the result is stored in the context.
    """
    # This is a simplified, mock JSON payload for an image message from LINE
    mock_webhook_body = f"""
    {{
        "destination": "Uxxxxxxxxx",
        "events": [
            {{
                "type": "message",
                "message": {{
                    "type": "image",
                    "id": "1234567890",
                    "contentProvider": {{
                        "type": "line"
                    }}
                }},
                "webhookEventId": "01H00000000000000000000000000000",
                "deliveryContext": {{ "isRedelivery": false }},
                "timestamp": 1625097600000,
                "source": {{
                    "type": "user",
                    "userId": "{line_user_id}"
                }},
                "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
                "mode": "active"
            }}
        ]
    }}
    """
    webhook_data = json.loads(mock_webhook_body)

    # In a real scenario, we would call a function to process this data.
    # For now, we'll just store the extracted info in the context.
    # We will be TDD'ing the function that does this logic.
    context.processed_event = {
        "line_user_id": webhook_data["events"][0]["source"]["userId"],
        "message_id": webhook_data["events"][0]["message"]["id"]
    }


@then('the system should identify the user as "{app_user}"')
def step_impl(context, app_user):
    """
    Checks if the user from the webhook was correctly mapped to an app user.
    """
    line_id = context.processed_event['line_user_id']
    identified_user = context.line_user_map.get(line_id)
    assert identified_user == app_user, f"Expected user '{app_user}', but identified '{identified_user}'"

@then('the image content should be queued for upload to "{group_name}"')
def step_impl(context, group_name):
    """
    Checks if the identified image and user group are prepared for the next stage.
    """
    # This is our intentional failure to drive the TDD cycle.
    # We need to build the logic that connects the identified user to their group
    # and prepares the image content for upload.
    assert False, "Image queueing logic not implemented yet"