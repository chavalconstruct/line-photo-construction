from typing import Dict, Optional, Any
import time

class StateManager:
    """Manages user sessions for multi-step interactions like photo uploads.

    This class keeps track of which users have an active session, what group
    they are uploading to, and when their session will expire. It uses in-memory
    storage with timestamps.

    Attributes:
        SESSION_DURATION_SECONDS: The default lifetime of a session in seconds.
    """
    # Default session time: 10 minutes (600 seconds)
    SESSION_DURATION_SECONDS = 600

    def __init__(self, session_duration_seconds: int = SESSION_DURATION_SECONDS) -> None:
        self._pending_uploads: Dict[str, Dict[str, Any]] = {}
        self.SESSION_DURATION_SECONDS = session_duration_seconds

    def set_pending_upload(self, user_id: str, group_name: str) -> None:
        """Starts or refreshes an upload session for a specific user.

        When a user sends a valid secret code, this method is called to record
        their session, associating their user ID with a target group and a
        fresh timestamp.

        Args:
            user_id: The unique identifier for the LINE user.
            group_name: The target folder/group name for subsequent uploads.
        """
        self._pending_uploads[user_id] = {
            "group_name": group_name,
            "timestamp": time.time()
        }
        print(f"Session started for user {user_id} in group {group_name}")

    def get_active_group(self, user_id: str) -> Optional[str]:
        """Retrieves the active group for a user if their session is valid.

        Checks if a user has a session and if it has not expired. If the
        session is expired, it's cleared, and None is returned.

        Args:
            user_id: The unique identifier for the LINE user.

        Returns:
            The group name as a string if the session is active, otherwise None.
        """
        session_data: Optional[Dict[str, Any]] = self._pending_uploads.get(user_id)
        if not session_data:
            return None

        elapsed_time: float = time.time() - session_data["timestamp"]
        if elapsed_time > self.SESSION_DURATION_SECONDS:
            # Session expired, clear it and return None
            del self._pending_uploads[user_id]
            print(f"Session for user {user_id} has expired.")
            return None
        
        # Session is active, return the group name
        return session_data["group_name"]

    def refresh_session(self, user_id: str)-> None:
        """Updates a user's session timestamp to prevent it from expiring.

        This should be called after a successful user action within a session,
        such as uploading a photo or saving a note.

        Args:
            user_id: The unique identifier for the LINE user whose session
                needs to be refreshed.
        """  
        if user_id in self._pending_uploads:
            self._pending_uploads[user_id]['timestamp'] = time.time()
            print(f"Session for user {user_id} has been refreshed.")