import os
import shutil
import json
from unittest.mock import patch, AsyncMock
from src.state_manager import StateManager

# --- NEW: Define paths for the template and the active config ---
CONFIG_TEMPLATE_PATH = "config.json.template"
CONFIG_FILE_PATH = "config.json"

def before_feature(context, feature):
    """
    Runs before each feature file to set a context name.
    """
    if "process_line_images.feature" in feature.filename:
        context.feature_name = "line_integration"
    elif "manage_codes.feature" in feature.filename:
        context.feature_name = "management"
    else:
        context.feature_name = "classification"

def before_scenario(context, scenario):
    """
    Runs before each scenario.
    """
    context.state_manager = StateManager()

    if context.feature_name == "management":
        # --- THIS IS THE NEW ROBUST SETUP ---
        # It copies the pristine template to the active config file,
        # ensuring every scenario starts with a clean state.
        if os.path.exists(CONFIG_TEMPLATE_PATH):
            shutil.copy(CONFIG_TEMPLATE_PATH, CONFIG_FILE_PATH)
        else:
            raise FileNotFoundError(f"Config template not found at {CONFIG_TEMPLATE_PATH}")
        # ------------------------------------

    elif context.feature_name == "line_integration":
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
    The config file restoration is no longer needed here.
    """
    if context.feature_name == "line_integration":
        context.patcher_gdrive.stop()
        context.patcher_download.stop()
    # No cleanup needed for 'management' as 'before_scenario' handles it.