import json
from typing import Optional, Dict, List, Any

class ConfigManager:
    """Handles loading, accessing, and modifying application configuration.

    This class provides a structured way to interact with configuration data
    (e.g., secret codes, admin users) loaded from a dictionary, abstracting
    the underlying data structure.
    """
    def __init__(self, config_data: dict) -> None:
        self._config_data: Dict[str, Any] = config_data
        self._secret_code_map: Dict[str, str] = self._config_data.get("secret_code_map", {})
        # self._line_user_map has been removed
        self._admins: List[str] = self._config_data.get("admins", [])

    def get_group_from_secret_code(self, code: str) -> Optional[str]:
        """Finds the group name associated with a given secret code.

        Args:
            code: The secret code string sent by the user.

        Returns:
            The corresponding group name if the code is found, otherwise None.
        """
        return self._secret_code_map.get(code)
    
    def get_all_secret_codes(self) -> Dict[str, str]:
        """Returns the entire dictionary of secret codes and their groups."""
        return self._secret_code_map

    # REMOVED: get_app_user method

    def is_admin(self, line_user_id: str) -> bool:
        """Checks if a given LINE user ID belongs to an administrator.

        Args:
            line_user_id: The user ID to check.

        Returns:
            True if the user is in the admin list, False otherwise.
        """
        return line_user_id in self._admins

    def add_secret_code(self, code: str, group: str):
        """Adds or updates a secret code in the configuration."""
        self._secret_code_map[code] = group
        print(f"Updated config: Added/updated code '{code}' for group '{group}'")

    def remove_secret_code(self, code: str) -> bool:
        """
        Removes a secret code from the configuration if it exists.
        Returns True if removal was successful, False otherwise.
        """
        if code in self._secret_code_map:
            del self._secret_code_map[code]
            print(f"Updated config: Removed code '{code}'")
            return True
        return False

    def save_config(self, file_path: str):
        """Saves the current configuration state to a JSON file.

        Writes the potentially modified secret code map and admin list back
        to a specified file path with indentation for readability.

        Args:
            file_path: The full path to the configuration file to be saved.
        """
        self._config_data["secret_code_map"] = self._secret_code_map
        self._config_data["admins"] = self._admins
        
        with open(file_path, 'w') as f:
            json.dump(self._config_data, f, indent=2)
        print(f"Configuration saved to {file_path}")