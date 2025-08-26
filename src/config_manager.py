from typing import Optional

class ConfigManager:
    """Handles loading and accessing application configuration."""
    def __init__(self, config_data: dict):
        self._secret_code_map = config_data.get("secret_code_map", {})
        self._line_user_map = config_data.get("line_user_map", {})

    def get_group_from_secret_code(self, code: str) -> Optional[str]:
        """Finds the group name associated with a given secret code."""
        return self._secret_code_map.get(code)

    def get_app_user(self, line_user_id: str) -> Optional[str]:
        """Finds the application user name from a LINE user ID."""
        return self._line_user_map.get(line_user_id)