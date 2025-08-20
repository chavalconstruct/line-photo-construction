"""
This module contains the logic for processing webhook events from the LINE API.
"""

def process_webhook_event(event, line_user_map, user_configs):
    """
    Processes a single event from a LINE webhook payload.

    It identifies the application user, finds their group, and extracts
    the image message ID.

    Args:
        event (dict): The event object from the LINE webhook payload.
        line_user_map (dict): A mapping of LINE User IDs to application usernames.
        user_configs (dict): A mapping of application usernames to their groups.

    Returns:
        dict: A dictionary with 'app_user', 'group', and 'image_message_id'
              if the user and message are valid.
        None: If the user is not found or the message is not an image.
    """
    # Ensure the message is an image
    if event.get("message", {}).get("type") != "image":
        return None

    # Extract the LINE User ID from the event
    line_user_id = event.get("source", {}).get("userId")
    if not line_user_id:
        return None

    # Find the application user from the mapping
    app_user = line_user_map.get(line_user_id)
    if not app_user:
        # This handles the 'test_process_event_with_unknown_user_returns_none' case
        return None

    # Find the user's group
    group = user_configs.get(app_user)
    if not group:
        return None

    # Extract the image message ID
    image_message_id = event.get("message", {}).get("id")

    # This dictionary is exactly what the first test case asserts
    return {
        "app_user": app_user,
        "group": group,
        "image_message_id": image_message_id
    }