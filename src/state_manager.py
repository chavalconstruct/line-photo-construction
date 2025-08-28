from typing import Dict, Optional, Any
import time

class StateManager:
    """
    Manages the state of users who are in an active image upload session.
    This implementation uses timestamps to handle session expiration.
    """
    # Default session time: 10 minutes (600 seconds)
    SESSION_DURATION_SECONDS = 600

    def __init__(self, session_duration_seconds: int = SESSION_DURATION_SECONDS):
        self._pending_uploads: Dict[str, Dict[str, Any]] = {}
        self.SESSION_DURATION_SECONDS = session_duration_seconds

    def set_pending_upload(self, user_id: str, group_name: str):
        """
        Starts or resets an upload session for a user.

        Args:
            user_id: The LINE user ID.
            group_name: The name of the target group/folder.
        """
        self._pending_uploads[user_id] = {
            "group": group_name,
            "timestamp": time.time()
        }
        print(f"Session started for user {user_id} in group {group_name}")

    def get_active_group(self, user_id: str) -> Optional[str]:
        """
        Retrieves the group for a user if their session is still active.
        If the session has expired, it is cleared.

        Args:
            user_id: The LINE user ID.

        Returns:
            The group name if the session is active, otherwise None.
        """
        session_data = self._pending_uploads.get(user_id)
        if not session_data:
            return None

        elapsed_time = time.time() - session_data["timestamp"]
        if elapsed_time > self.SESSION_DURATION_SECONDS:
            # Session expired, clear it and return None
            del self._pending_uploads[user_id]
            print(f"Session for user {user_id} has expired.")
            return None
        
        # Session is active, return the group name
        return session_data["group"]

    def refresh_session(self, user_id: str):
        """
        Refreshes the session timestamp for a user to the current time.
        This is typically called after a successful action, like an image upload.
        """
        if user_id in self._pending_uploads:
            self._pending_uploads[user_id]['timestamp'] = time.time()
            print(f"Session for user {user_id} has been refreshed.")