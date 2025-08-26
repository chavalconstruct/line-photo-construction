import os
import shutil
import json # <-- IMPORT JSON
from unittest.mock import patch, AsyncMock
from src.state_manager import StateManager

CONFIG_FILE_PATH = "config.json" # <-- DEFINE CONFIG PATH

def before_feature(context, feature):
    """
    Runs before each feature file.
    """
    if "process_line_images.feature" in feature.filename:
        context.feature_name = "line_integration"
    elif "manage_codes.feature" in feature.filename:
        context.feature_name = "management"
        # --- NEW: Backup config data before running this feature ---
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                context.original_config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # In case the file is missing or broken, store None
            context.original_config_data = None
        # ----------------------------------------------------------
    else:
        context.feature_name = "classification"

def before_scenario(context, scenario):
    """
    Runs before each scenario.
    """
    context.state_manager = StateManager()

    if context.feature_name == "line_integration":
        context.patcher_gdrive = patch('src.webhook_processor.GoogleDriveService')
        context.patcher_download = patch('src.webhook_processor.download_image_content', new_callable=AsyncMock)
        MockGoogleDriveService = context.patcher_gdrive.start()
        context.mock_gdrive_service = MockGoogleDriveService.return_value
        context.mock_download = context.patcher_download.start()
    
    elif context.feature_name == "classification":
        if os.path.exists("Group A"): shutil.rmtree("Group A")
        if os.path.exists("Group B"): shutil.rmtree("Group B")

def after_scenario(context, scenario):
    """
    Runs after each scenario to clean up.
    """
    if context.feature_name == "line_integration":
        context.patcher_gdrive.stop()
        context.patcher_download.stop()
    elif context.feature_name == "management":
        # --- NEW: Restore the original config data ---
        if hasattr(context, 'original_config_data') and context.original_config_data is not None:
            with open(CONFIG_FILE_PATH, 'w') as f:
                json.dump(context.original_config_data, f, indent=2)
        # ---------------------------------------------