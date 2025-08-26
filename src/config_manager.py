import json
from typing import Optional, Dict

class ConfigManager:
    """Handles loading, accessing, and modifying application configuration."""
    def __init__(self, config_data: dict):
        self._config_data = config_data
        self._secret_code_map = self._config_data.get("secret_code_map", {})
        self._line_user_map = self._config_data.get("line_user_map", {})
        self._admins = self._config_data.get("admins", [])

    def get_group_from_secret_code(self, code: str) -> Optional[str]:
        """Finds the group name associated with a given secret code."""
        return self._secret_code_map.get(code)

    def get_app_user(self, line_user_id: str) -> Optional[str]:
        """Finds the application user name from a LINE user ID."""
        return self._line_user_map.get(line_user_id)

    # --- NEW METHODS ---

    def is_admin(self, line_user_id: str) -> bool:
        """Checks if a given LINE user ID belongs to an admin."""
        return line_user_id in self._admins

    def add_secret_code(self, code: str, group: str):
        """Adds or updates a secret code in the configuration."""
        self._secret_code_map[code] = group
        print(f"Updated config: Added/updated code '{code}' for group '{group}'")

    def remove_secret_code(self, code: str):
        """Removes a secret code from the configuration if it exists."""
        if code in self._secret_code_map:
            del self._secret_code_map[code]
            print(f"Updated config: Removed code '{code}'")

    def save_config(self, file_path: str):
        """Saves the current configuration data to a file."""
        # Reconstruct the main dictionary before saving
        self._config_data["secret_code_map"] = self._secret_code_map
        self._config_data["admins"] = self._admins
        # (line_user_map is usually static, but good practice to include it)
        self._config_data["line_user_map"] = self._line_user_map

        with open(file_path, 'w') as f:
            json.dump(self._config_data, f, indent=2)
        print(f"Configuration saved to {file_path}")