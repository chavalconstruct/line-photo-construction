from typing import Dict, Optional

class StateManager:
    """
    Manages the state of users who are pending an image upload.
    This is a simple in-memory implementation using a dictionary.
    """
    def __init__(self):
        self._pending_uploads: Dict[str, str] = {}

    def set_pending_upload(self, user_id: str, group_name: str):
        """
        Records that a user is expecting to upload an image to a specific group.

        Args:
            user_id: The LINE user ID.
            group_name: The name of the target group/folder.
        """
        self._pending_uploads[user_id] = group_name
        print(f"State set: User {user_id} is pending upload to {group_name}")

    def consume_pending_upload(self, user_id: str) -> Optional[str]:
        """
        Retrieves the pending group for a user and clears their state.
        This ensures the state is used only once.

        Args:
            user_id: The LINE user ID.

        Returns:
            The name of the group if the user was in a pending state, otherwise None.
        """
        return self._pending_uploads.pop(user_id, None)

