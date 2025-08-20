import unittest

# This import will fail initially, which is what we want.
from src.webhook_processor import process_webhook_event

class TestWebhookProcessor(unittest.TestCase):
    """
    Tests the webhook processing logic.
    """

    def test_process_event_identifies_user_and_group(self):
        """
        Ensures the function correctly maps a LINE user ID to a user,
        finds their group, and extracts the image message ID.
        """
        # 1. Setup: Define the inputs for our function
        
        # A mock of the essential data extracted from a webhook
        event_data = {
            "source": { "type": "user", "userId": "U12345abcde" },
            "message": { "type": "image", "id": "msg_id_9876" }
        }
        
        # The user mapping configurations
        line_user_map = {"U12345abcde": "Somchai"}
        user_configs = {"Somchai": "Group A"}

        # 2. Action: Call the function we intend to build
        result = process_webhook_event(
            event=event_data,
            line_user_map=line_user_map,
            user_configs=user_configs
        )

        # 3. Assert: Check if the output is what we expect
        self.assertIsNotNone(result)
        self.assertEqual(result['app_user'], "Somchai")
        self.assertEqual(result['group'], "Group A")
        self.assertEqual(result['image_message_id'], "msg_id_9876")
        
    def test_process_event_with_unknown_user_returns_none(self):
        """
        Ensures that if the LINE user is not in our mapping,
        the function returns None.
        """
        # 1. Setup
        event_data = {
            "source": { "type": "user", "userId": "U_unknown_user" },
            "message": { "type": "image", "id": "msg_id_1111" }
        }
        line_user_map = {"U12345abcde": "Somchai"}
        user_configs = {"Somchai": "Group A"}

        # 2. Action
        result = process_webhook_event(
            event=event_data,
            line_user_map=line_user_map,
            user_configs=user_configs
        )

        # 3. Assert
        self.assertIsNone(result)