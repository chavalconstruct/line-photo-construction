import re
from typing import Optional, Dict

def parse_command(text: str) -> Optional[Dict[str, str]]:
    """
    Parses a text message to see if it matches a known admin command format.
    
    Args:
        text: The input text message from the user.
        
    Returns:
        A dictionary with 'action' and its parameters if it's a valid command,
        otherwise None.
    """
    text = text.strip()

    # Pattern for "add code <code> for group <group>"
    add_pattern = re.compile(
        r"add\s+code\s+([#\w-]+)\s+for\s+group\s+([\w_]+)", re.IGNORECASE
    )
    
    # Pattern for "remove code <code>"
    remove_pattern = re.compile(
        r"remove\s+code\s+([#\w-]+)", re.IGNORECASE
    )

    # --- NEW PATTERN ---
    # Pattern for "list codes"
    list_pattern = re.compile(r"list\s+codes", re.IGNORECASE)
    # -------------------

    # Check for 'add' command
    match = add_pattern.fullmatch(text)
    if match:
        return {"action": "add", "code": match.group(1), "group": match.group(2)}

    # Check for 'remove' command
    match = remove_pattern.fullmatch(text)
    if match:
        return {"action": "remove", "code": match.group(1)}

    # --- NEW LOGIC ---
    # Check for 'list' command
    match = list_pattern.fullmatch(text)
    if match:
        return {"action": "list"}
    # -----------------

    # If no patterns match, it's not a command
    return None